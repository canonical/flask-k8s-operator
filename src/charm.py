#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging
import shlex
import typing

import ops
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
from charms.traefik_k8s.v1.ingress import IngressPerAppRequirer
from ops.main import main

from charm_state import CharmState
from constants import FLASK_CONTAINER_NAME, FLASK_SERVICE_NAME
from databases import Databases
from exceptions import (
    CharmConfigInvalidError,
    InvalidDatabaseRelationDataError,
    PebbleNotReadyError,
)
from flask_app import FlaskApp
from observability import Observability
from secret_storage import SecretStorage
from webserver import GunicornWebserver

logger = logging.getLogger(__name__)


class FlaskCharm(ops.CharmBase):
    """Flask Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self._databases = Databases(charm=self)
        self._secret_storage = SecretStorage(charm=self)

        try:
            self._charm_state = CharmState.from_charm(
                charm=self, secret_storage=self._secret_storage
            )
        except CharmConfigInvalidError as exc:
            self._update_app_and_unit_status(ops.BlockedStatus(exc.msg))
            return
        self._flask_app = FlaskApp(charm_state=self._charm_state)
        self._webserver = GunicornWebserver(
            charm_state=self._charm_state,
            flask_container=self.unit.get_container(FLASK_CONTAINER_NAME),
            flask_app=self._flask_app,
        )
        self._ingress = IngressPerAppRequirer(
            self,
            port=self._charm_state.flask_port,
            # We're forced to use the app's service endpoint
            # as the ingress per app interface currently always routes to the leader.
            # https://github.com/canonical/traefik-k8s-operator/issues/159
            host=f"{self.app.name}-endpoints.{self.model.name}.svc.cluster.local",
            strip_prefix=True,
        )
        self._observability = Observability(charm=self, charm_state=self._charm_state)

        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(
            self.on.statsd_prometheus_exporter_pebble_ready,
            self._on_statsd_prometheus_exporter_pebble_ready,
        )
        self.framework.observe(self.on.rotate_secret_key_action, self._on_rotate_secret_key_action)
        self.framework.observe(
            self.on.secret_storage_relation_changed, self._on_secret_storage_relation_changed
        )
        self._require_nginx_route()

    def _require_nginx_route(self) -> None:
        """Set up the requirer side of the nginx-route relation."""
        require_nginx_route(
            charm=self,
            service_name=self.app.name,
            service_hostname=self.app.name,
            service_port=self._charm_state.flask_port,
        )

    def _update_app_and_unit_status(self, status: ops.StatusBase) -> None:
        """Update the application and unit status.

        Args:
            status: the desired application and unit status.
        """
        self.unit.status = status
        if self.unit.is_leader():
            self.app.status = status

    def container(self) -> ops.Container:
        """Get the flask application workload container controller.

        Return:
            The controller of the flask application workload container.

        Raises:
            PebbleNotReadyError: if the pebble service inside the container is not ready while the
                ``require_connected`` is set to True.
        """
        if not self.unit.get_container(FLASK_CONTAINER_NAME).can_connect():
            raise PebbleNotReadyError("pebble inside flask-app container is not ready")

        container = self.unit.get_container(FLASK_CONTAINER_NAME)
        return container

    @property
    def _is_precondition_satisfied(self) -> bool:
        """Check if the precondition for the Flask application has been satisfied.

        Preconditions include:
            1. Flask workload container is ready
            2. Secret storage has been initialized

        Return:
            True if all preconditions is satisfied.
        """
        try:
            self.container()
        except PebbleNotReadyError:
            logger.info("pebble client in the Flask container is not ready")
            return False
        if not self._secret_storage.is_initialized:
            logger.info("secret storage is not initialized, defer config-changed")
            return False
        return True

    def _restart_flask_application(self) -> None:
        """Start or restart the flask application with the latest charm configuration.

        The flask charm must be ready (i.e. preconditions meet) before calling this function.
        """
        container = self.container()
        container.add_layer("flask-app", self._flask_layer(), combine=True)
        is_webserver_running = container.get_service(FLASK_SERVICE_NAME).is_running()
        try:
            self._webserver.update_config(is_webserver_running=is_webserver_running)
        except CharmConfigInvalidError as exc:
            self._update_app_and_unit_status(ops.BlockedStatus(exc.msg))
            return
        container.replan()
        self._update_app_and_unit_status(ops.ActiveStatus())

    def _on_config_changed(self, event: ops.EventBase) -> None:
        """Configure the flask pebble service layer.

        Args:
            event: the config-changed event that triggers this callback function.
        """
        if not self._is_precondition_satisfied:
            logger.info("charm hasn't finished the initialization, defer config-changed")
            event.defer()
            return
        self._restart_flask_application()

    def _flask_layer(self) -> dict:
        """Generate the pebble layer definition for flask application.

        Returns:
            The pebble layer definition for flask application.
        """
        environment = self._flask_app.flask_environment()
        try:
            environment.update(self._databases.get_uris())
        except InvalidDatabaseRelationDataError as exc:
            self._update_app_and_unit_status(ops.BlockedStatus(exc.msg))
            # Returning an empty dict will cancel add_layer() when used with combine=True
            return {}
        return {
            "services": {
                FLASK_SERVICE_NAME: {
                    "override": "replace",
                    "summary": "Flask application service",
                    "command": shlex.join(self._webserver.command),
                    "startup": "enabled",
                    "environment": environment,
                }
            },
        }

    def _on_statsd_prometheus_exporter_pebble_ready(self, _event: ops.PebbleReadyEvent) -> None:
        """Handle the statsd-prometheus-exporter-pebble-ready event."""
        statsd_container = self.unit.get_container("statsd-prometheus-exporter")
        statsd_layer = {
            "summary": "statsd exporter layer",
            "description": "statsd exporter layer",
            "services": {
                "statsd-prometheus-exporter": {
                    "override": "replace",
                    "summary": "statsd exporter service",
                    "user": "nobody",
                    "command": "/bin/statsd_exporter",
                    "startup": "enabled",
                }
            },
            "checks": {
                "container-ready": {
                    "override": "replace",
                    "level": "ready",
                    "http": {"url": "http://localhost:9102/metrics"},
                },
            },
        }
        statsd_container.add_layer("statsd-prometheus-exporter", statsd_layer, combine=True)
        statsd_container.replan()

    def _on_rotate_secret_key_action(self, event: ops.ActionEvent) -> None:
        """Handle the rotate-secret-key action.

        Args:
            event: the action event that trigger this callback.
        """
        if not self.unit.is_leader():
            event.fail("only leader unit can rotate secret key")
            return
        if not self._is_precondition_satisfied:
            event.fail("flask charm is still initializing")
            return
        self._secret_storage.reset_flask_secret_key()
        event.set_results({"status": "success"})
        self._restart_flask_application()

    def _on_secret_storage_relation_changed(self, event: ops.RelationEvent) -> None:
        """Handle the secret-storage-relation-changed event.

        Args:
            event: the action event that trigger this callback.
        """
        self._on_config_changed(event)


if __name__ == "__main__":  # pragma: nocover
    main(FlaskCharm)
