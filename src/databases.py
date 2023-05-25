# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the Databases class to handle database relations and state."""

import logging
import typing

import yaml
from charms.data_platform_libs.v0.data_interfaces import DatabaseRequires

from constants import FLASK_DATABASE_NAME
from exceptions import InvalidDatabaseRelationDataError

if typing.TYPE_CHECKING:
    from charm import FlaskCharm

logger = logging.getLogger(__name__)


class Databases:  # pylint: disable=too-few-public-methods
    """A class handling databases relations and state.

    Attrs:
        _charm: The main charm. Used for events callbacks
        _databases: A dict of DatabaseRequires to store relations
    """

    def __init__(self, charm: "FlaskCharm"):
        """Initialize a new instance of the Databases class.

        Args:
            charm: The main charm. Used for events callbacks
        """
        self._charm = charm

        with open("metadata.yaml", encoding="utf-8") as metadata_fo:
            metadata = yaml.safe_load(metadata_fo)
            self._db_interfaces = (
                name for name in list(metadata["requires"]) if name.startswith("db_")
            )

        self._databases: typing.Dict[str, DatabaseRequires] = {
            name: self._setup_database_requirer(name, FLASK_DATABASE_NAME)
            for name in self._db_interfaces
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
            self._charm,
            relation_name=relation_name,
            database_name=database_name,
        )
        self._charm.framework.observe(
            database_requirer.on.database_created, self._charm.on_config_changed
        )
        self._charm.framework.observe(
            self._charm.on[relation_name].relation_broken, self._charm.on_config_changed
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
            # see: metadata.yaml
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
            db_uris[f"{interface_name[3:].upper()}_DB_CONNECT_STRING"] = (
                f"{interface_name[3:]}://"
                f"{data['username']}:{data['password']}"
                f"@{endpoint}/{database_name}"
            )

        return db_uris
