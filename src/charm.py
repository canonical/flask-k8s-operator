#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging
import shlex
import typing

from charms.traefik_k8s.v1.ingress import IngressPerAppRequirer
from ops.charm import CharmBase, ConfigChangedEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, Container

from charm_state import CharmState
from exceptions import WebserverConfigInvalid
from webserver import GunicornWebserver

logger = logging.getLogger(__name__)


class FlaskCharm(CharmBase):
    """Flask Charm service."""

    _FLASK_CONTAINER_NAME = "flask-app"
    _FLASK_APP_PORT = 8000
    _SERVICE_NAME = "flask-app"

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self._charm_state = CharmState.from_charm(charm=self)
        self._webserver = GunicornWebserver(
            charm_state=self._charm_state,
            flask_container=self.unit.get_container(self._FLASK_CONTAINER_NAME),
        )
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.ingress = IngressPerAppRequirer(
            self,
            port=self._FLASK_APP_PORT,
            # We're forced to use the app's service endpoint
            # as the ingress per app interface currently always routes to the leader.
            # https://github.com/canonical/traefik-k8s-operator/issues/159
            host=f"{self.app.name}-endpoints.{self.model.name}.svc.cluster.local",
            strip_prefix=True,
        )

    def container_can_connect(self) -> bool:
        """Check if the Flask pebble service is connectable.

        Returns:
            True if the Flask pebble service is connectable, False otherwise.
        """
        return self.unit.get_container(self._FLASK_CONTAINER_NAME).can_connect()

    def container(self) -> Container:
        """Get the flask application workload container controller.

        Return:
            The controller of the flask application workload container.

        Raises:
            RuntimeError: if the pebble service inside the container is not ready while the
                ``require_connected`` is set to True.
        """
        if not self.container_can_connect():
            raise RuntimeError("pebble inside flask-app container is not ready")

        container = self.unit.get_container(self._FLASK_CONTAINER_NAME)
        return container

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Configure the flask pebble service layer.

        Args:
            event: the config-changed event that trigger this callback function.
        """
        if not self.container_can_connect():
            event.defer()
            return

        container = self.container()
        container.add_layer("flask-app", self.flask_layer(), combine=True)
        is_webserver_running = container.get_service(self._SERVICE_NAME).is_running()
        try:
            self._webserver.update_config(is_webserver_running=is_webserver_running)
        except WebserverConfigInvalid as exc:
            self.unit.status = BlockedStatus(exc.msg)
            return
        container.replan()
        self.unit.status = ActiveStatus()

    def flask_layer(self) -> dict:
        """Generate the pebble layer definition for flask application.

        Returns:
            The pebble layer definition for flask application.
        """
        return {
            "services": {
                "flask-app": {
                    "override": "replace",
                    "summary": "Flask application service",
                    "command": shlex.join(self._webserver.command),
                    "user": "flask",
                    "group": "flask",
                    "startup": "enabled",
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    main(FlaskCharm)
