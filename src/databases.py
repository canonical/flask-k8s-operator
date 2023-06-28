# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the Databases class to handle database relations and state."""

import logging
import pathlib
import typing

import yaml
from charms.data_platform_libs.v0.data_interfaces import DatabaseRequires, DatabaseRequiresEvent
from ops import CharmBase, Object

from constants import (
    FLASK_CONTAINER_NAME,
    FLASK_DATABASE_NAME,
    FLASK_SERVICE_NAME,
    FLASK_SUPPORTED_DB_INTERFACES,
)
from exceptions import InvalidDatabaseRelationDataError, PebbleNotReadyError

logger = logging.getLogger(__name__)


# We need to derive from ops.framework.Object to subscribe to callbacks
# from ops.framework. See: https://github.com/canonical/operator/blob/main/ops/framework.py#L782
class Databases(Object):  # pylint: disable=too-few-public-methods
    """A class handling databases relations and state.

    Attrs:
        _charm: The main charm. Used for events callbacks
        _databases: A dict of DatabaseRequires to store relations
    """

    def __init__(self, charm: CharmBase):
        """Initialize a new instance of the Databases class.

        Args:
            charm: The main charm. Used for events callbacks
        """
        # The following is necessary to be able to subscribe to callbacks from ops.framework
        super().__init__(charm, "databases")
        self._charm = charm

        metadata = yaml.safe_load(pathlib.Path("metadata.yaml").read_text(encoding="utf-8"))
        self._db_interfaces = (
            FLASK_SUPPORTED_DB_INTERFACES[require["interface"]]
            for require in metadata["requires"].values()
            if require["interface"] in FLASK_SUPPORTED_DB_INTERFACES
        )
        # automatically create database relation requirers to manage database relations
        self._databases: typing.Dict[str, DatabaseRequires] = {
            name: self._setup_database_requirer(name, FLASK_DATABASE_NAME)
            for name in self._db_interfaces
        }

    def _on_database_requires_event(self, event: DatabaseRequiresEvent) -> None:
        """Configure the flask pebble service layer in case of DatabaseRequiresEvent.

        Args:
            event: the database-requires-changed event that trigger this callback function.
        """
        try:
            container = self._charm.unit.get_container(FLASK_CONTAINER_NAME)
        except PebbleNotReadyError:
            logger.info(
                "pebble client in the Flask container is not ready, defer database-requires-event"
            )
            event.defer()
            return
        plan = container.get_plan()
        if FLASK_SERVICE_NAME in plan.services:
            flask_service = plan.services[FLASK_SERVICE_NAME].to_dict()
            flask_service["environment"].update(self.get_uris())
            new_layer = {
                "services": {
                    FLASK_SERVICE_NAME: flask_service,
                },
            }
            container.add_layer("flask-app", new_layer, combine=True)
        container.replan()

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
            self._charm,
            relation_name=relation_name,
            database_name=database_name,
        )
        self._charm.framework.observe(
            database_requirer.on.database_created, self._on_database_requires_event
        )
        self._charm.framework.observe(
            self._charm.on[relation_name].relation_broken, self._on_database_requires_event
        )
        return database_requirer

    def get_uris(self) -> typing.Dict[str, str]:
        """Compute DatabaseURI and return it.

        Returns:
            DatabaseURI containing details about the data provider integration

        Raises:
            InvalidDatabaseRelationDataError: if the database relation has invalid data
        """
        db_uris: typing.Dict[str, str] = {}

        # the database requires could not be defined
        # if get_uris() is called before their initialization
        if not hasattr(self, "_databases") or not self._databases:
            return db_uris

        for interface_name, db_requires in self._databases.items():
            relation_data = list(db_requires.fetch_relation_data().values())

            if not relation_data:
                continue

            # There can be only one database integrated at a time
            # with the same interface name. See: metadata.yaml
            data = relation_data[0]

            # Check that the relation data is well formed according to the following json_schema:
            # https://github.com/canonical/charm-relation-interfaces/blob/main/interfaces/mysql_client/v0/schemas/provider.json
            if not all(data.get(key) for key in ("endpoints", "username", "password")):
                logger.warning("Incorrect relation data from the data provider: %s", data)
                raise InvalidDatabaseRelationDataError(
                    f"Incorrect relation data from the data provider: {data}"
                )

            database_name = data.get("database", db_requires.database)
            endpoint = data["endpoints"].split(",")[0]
            db_uris[f"{interface_name.upper()}_DB_CONNECT_STRING"] = (
                f"{interface_name}://"
                f"{data['username']}:{data['password']}"
                f"@{endpoint}/{database_name}"
            )

        return db_uris
