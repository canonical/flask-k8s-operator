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
from ops.model import ActiveStatus, BlockedStatus, Container

from charm_state import CharmState
from consts import FLASK_APP_PORT, FLASK_CONTAINER_NAME, FLASK_SERVICE_NAME
from exceptions import WebserverConfigInvalidError
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
        self._charm_state = CharmState.from_charm(charm=self)
        self._webserver = GunicornWebserver(
            charm_state=self._charm_state,
            flask_container=self.unit.get_container(FLASK_CONTAINER_NAME),
        )
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.ingress = IngressPerAppRequirer(
            self,
            port=FLASK_APP_PORT,
            # We're forced to use the app's service endpoint
            # as the ingress per app interface currently always routes to the leader.
            # https://github.com/canonical/traefik-k8s-operator/issues/159
            host=f"{self.app.name}-endpoints.{self.model.name}.svc.cluster.local",
            strip_prefix=True,
        )
        self.database_requirer: DatabaseRequires = self._setup_database_requirer(
            "database", "flask-app"
        )

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
            RuntimeError: if the pebble service inside the container is not ready while the
                ``require_connected`` is set to True.
        """
        if not self.container_can_connect():
            raise RuntimeError("pebble inside flask-app container is not ready")

        container = self.unit.get_container(FLASK_CONTAINER_NAME)
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
        is_webserver_running = container.get_service(FLASK_SERVICE_NAME).is_running()
        try:
            self._webserver.update_config(is_webserver_running=is_webserver_running)
        except WebserverConfigInvalidError as exc:
            self.unit.status = BlockedStatus(exc.msg)
            return
        container.replan()
        self.unit.status = ActiveStatus()

    def _database_uri(self) -> str:
        """Compute DatabaseURI and return it.

        Returns:
            DatabaseURI containing details about the data provider integration
        """
        # the database_requirer could not be defined
        # if _database_uri() is called before its initialization
        if not hasattr(self, "database_requirer") or not self.database_requirer:
            return ""

        relations_data = list(self.database_requirer.fetch_relation_data().values())

        if not relations_data:
            logger.warning("No relation data from database provider")
            return ""

        # There can be only one database integrated at a time
        # see: metadata.yaml
        data = relations_data[0]

        # Let's check that the relation data is well formed according to the following json_schema:
        # https://github.com/canonical/charm-relation-interfaces/blob/main/interfaces/mysql_client/v0/schemas/provider.json
        if not all(data.get(key) for key in ("endpoints", "username", "password")):
            logger.warning("Incorrect relation data from the data provider: %s", data)
            return ""

        database_name = data.get("database", self.database_requirer.database)
        endpoint = data["endpoints"].split(",")[0]
        return f"mysql://{data['username']}:{data['password']}@{endpoint}/{database_name}"

    def _get_flask_env_config(self) -> dict[str, str]:
        """Return an envConfig with some core configuration.

        Returns:
            Dictionary with the environment variables for the container.
        """
        env_config: dict[str, str] = {
            "FLASK_DATABASE_URI": self._database_uri(),
        }
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
