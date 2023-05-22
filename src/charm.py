#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging
import shlex
import typing

from charms.data_platform_libs.v0.data_interfaces import DatabaseRequires
from charms.traefik_k8s.v1.ingress import IngressPerAppRequirer
from ops.charm import CharmBase, ConfigChangedEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, Container, StatusBase

from charm_state import CharmState
from constants import FLASK_CONTAINER_NAME, FLASK_SERVICE_NAME
from exceptions import CharmConfigInvalidError, PebbleNotReadyError
from flask_app import FlaskApp
from webserver import GunicornWebserver

logger = logging.getLogger(__name__)


class FlaskCharm(CharmBase):
    """Flask Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        try:
            self._charm_state = CharmState.from_charm(charm=self)
        except CharmConfigInvalidError as exc:
            self._update_app_and_unit_status(BlockedStatus(exc.msg))
            return
        self._webserver = GunicornWebserver(
            charm_state=self._charm_state,
            flask_container=self.unit.get_container(FLASK_CONTAINER_NAME),
        )
        self._flask_app = FlaskApp(charm_state=self._charm_state)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.ingress = IngressPerAppRequirer(
            self,
            port=self._charm_state.flask_port,
            # We're forced to use the app's service endpoint
            # as the ingress per app interface currently always routes to the leader.
            # https://github.com/canonical/traefik-k8s-operator/issues/159
            host=f"{self.app.name}-endpoints.{self.model.name}.svc.cluster.local",
            strip_prefix=True,
        )
        self.databases: typing.Dict[str, DatabaseRequires] = {
            name: self._setup_database_requirer(name, "flask-app")
            for name in ("mysql", "postgresql")
        }

    def _setup_database_requirer(self, relation_name: str, database_name: str) -> DatabaseRequires:
        """Set up a DatabaseRequires instance.

        The DatabaseRequires instance is an interface between the charm and various data providers.
        It handles those relations and emit events to help us abstract these integrations.

        Args:
            relation_name: Name of the data relation
            database_name: Name of the database (can be overwritten by the provider)

        Returns:
            DatabaseRequires object produced by the data_platform_libs.v0.data_interfaces library
        """
        database_requirer = DatabaseRequires(
            self,
            relation_name=relation_name,
            database_name=database_name,
        )
        self.framework.observe(database_requirer.on.database_created, self._on_config_changed)
        self.framework.observe(self.on[relation_name].relation_broken, self._on_config_changed)
        return database_requirer

    def _update_app_and_unit_status(self, status: StatusBase) -> None:
        """Update the application and unit status.

        Args:
            status: the desired application and unit status.
        """
        self.unit.status = status
        if self.unit.is_leader():
            self.app.status = status

    def container_can_connect(self) -> bool:
        """Check if the Flask pebble service is connectable.

        Returns:
            True if the Flask pebble service is connectable, False otherwise.
        """
        return self.unit.get_container(FLASK_CONTAINER_NAME).can_connect()

    def container(self) -> Container:
        """Get the flask application workload container controller.

        Return:
            The controller of the flask application workload container.

        Raises:
            PebbleNotReadyError: if the pebble service inside the container is not ready while the
                ``require_connected`` is set to True.
        """
        if not self.container_can_connect():
            raise PebbleNotReadyError("pebble inside flask-app container is not ready")

        container = self.unit.get_container(FLASK_CONTAINER_NAME)
        return container

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Configure the flask pebble service layer.

        Args:
            event: the config-changed event that trigger this callback function.
        """
        try:
            container = self.container()
        except PebbleNotReadyError:
            logger.info("pebble client in the Flask container is not ready, defer config-changed")
            event.defer()
            return
        container.add_layer("flask-app", self.flask_layer(), combine=True)
        is_webserver_running = container.get_service(FLASK_SERVICE_NAME).is_running()
        try:
            self._webserver.update_config(is_webserver_running=is_webserver_running)
        except CharmConfigInvalidError as exc:
            self._update_app_and_unit_status(BlockedStatus(exc.msg))
            return
        container.replan()
        self._update_app_and_unit_status(ActiveStatus())

    def _database_uri(self) -> typing.Dict[str, str]:
        """Compute DatabaseURI and return it.

        Returns:
            DatabaseURI containing details about the data provider integration
        """
        db_uris: typing.Dict[str, str] = {}

        # the database_requirer could not be defined
        # if _database_uri() is called before its initialization
        if not hasattr(self, "databases") or not self.databases:
            return db_uris

        for database, db_requires in self.databases.items():
            relation_data = list(db_requires.fetch_relation_data().values())

            if not relation_data:
                continue

            # There can be only one database integrated at a time
            # see: metadata.yaml
            data = relation_data[0]

            # Check that the relation data is well formed according to the following json_schema:
            # https://github.com/canonical/charm-relation-interfaces/blob/main/interfaces/mysql_client/v0/schemas/provider.json
            if not all(data.get(key) for key in ("endpoints", "username", "password")):
                logger.warning("Incorrect relation data from the data provider: %s", data)
                continue

            database_name = data.get("database", db_requires.database)
            endpoint = data["endpoints"].split(",")[0]
            db_uris[database] = (
                f"{database}://"
                f"{data['username']}:{data['password']}"
                f"@{endpoint}/{database_name}"
            )

        return db_uris

    def _get_flask_env_config(self) -> dict[str, str]:
        """Return an envConfig with some core configuration.

        Returns:
            Dictionary with the environment variables for the container.
        """
        env_config: typing.Dict[str, str] = {}
        env_config.update(
            {
                f"FLASK_{db_name.upper()}_DB_CONNECT_STRING": db_uri
                for (db_name, db_uri) in self._database_uri().items()
            }
        )
        env_config.update(self._flask_app.flask_environment)
        return env_config

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
                    "startup": "enabled",
                    "environment": self._get_flask_env_config(),
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    main(FlaskCharm)
