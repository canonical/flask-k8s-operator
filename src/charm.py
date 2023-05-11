#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging
import typing

from charms.data_platform_libs.v0.data_interfaces import DatabaseRequires
from charms.traefik_k8s.v1.ingress import IngressPerAppRequirer
from ops.charm import CharmBase, ConfigChangedEvent
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class FlaskCharm(CharmBase):
    """Flask Charm service."""

    _FLASK_APP_PORT = 8000

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self.config_service)
        self.ingress = IngressPerAppRequirer(
            self,
            port=self._FLASK_APP_PORT,
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
        self.framework.observe(database_requirer.on.database_created, self.config_service)
        self.framework.observe(self.on[relation_name].relation_broken, self.config_service)
        return database_requirer

    def config_service(self, event: ConfigChangedEvent) -> None:
        """Configure the flask pebble service layer.

        Args:
            event: the config-changed event that trigger this callback function.
        """
        container = self.unit.get_container("flask-app")
        if not container.can_connect():
            event.defer()
            return
        container.add_layer("flask-app", self._flask_layer(), combine=True)
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
        return f"mysql://{data['username']}:{data['password']}:{endpoint}/{database_name}"

    def _get_flask_env_config(self) -> dict[str, str]:
        """Return an envConfig with some core configuration.

        Returns:
            Dictionary with the environment variables for the container.
        """
        env_config: dict[str, str] = {
            "FLASK_DATABASE_URI": self._database_uri(),
        }
        return env_config

    def _flask_layer(self) -> dict:
        """Generate the pebble layer definition for flask application.

        Returns:
            The pebble layer definition for flask application.
        """
        return {
            "services": {
                "flask-app": {
                    "override": "replace",
                    "summary": "Flask application service",
                    "command": (
                        "/bin/python3 -m gunicorn --chdir /srv/flask/app app:app"
                        f" -b 0.0.0.0:{self._FLASK_APP_PORT}"
                    ),
                    "startup": "enabled",
                    "environment": self._get_flask_env_config(),
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    main(FlaskCharm)
