# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm database relations unit tests."""

import unittest.mock

import pytest
from ops.model import Container
from ops.testing import Harness

from constants import FLASK_CONTAINER_NAME, FLASK_DATABASE_NAME
from databases import Databases


@pytest.mark.parametrize(
    "relations, expected_output",
    [
        (
            (
                {
                    "interface": "db_mysql",
                    "data": {
                        "endpoints": "test-mysql:3306",
                        "password": "test-password",
                        "username": "test-username",
                    },
                },
            ),
            {
                "MYSQL_DB_CONNECT_STRING": (
                    "mysql://test-username:test-password@test-mysql:3306/flask-app"
                )
            },
        ),
        (
            (
                {
                    "interface": "db_postgresql",
                    "data": {
                        "database": "test-database",
                        "endpoints": "test-postgresql:5432,test-postgresql-2:5432",
                        "password": "test-password",
                        "username": "test-username",
                    },
                },
            ),
            {
                "POSTGRESQL_DB_CONNECT_STRING": (
                    "postgresql://test-username:test-password"
                    "@test-postgresql:5432/test-database"
                )
            },
        ),
        (
            (
                {
                    "interface": "db_mysql",
                    "data": {
                        "endpoints": "test-mysql:3306",
                        "password": "test-password",
                        "username": "test-username",
                    },
                },
                {
                    "interface": "db_postgresql",
                    "data": {
                        "database": "test-database",
                        "endpoints": "test-postgresql:5432,test-postgresql-2:5432",
                        "password": "test-password",
                        "username": "test-username",
                    },
                },
            ),
            {
                "MYSQL_DB_CONNECT_STRING": (
                    "mysql://test-username:test-password@test-mysql:3306/flask-app"
                ),
                "POSTGRESQL_DB_CONNECT_STRING": (
                    "postgresql://test-username:test-password"
                    "@test-postgresql:5432/test-database"
                ),
            },
        ),
    ],
)
def test_database_uri_mocked(
    monkeypatch: pytest.MonkeyPatch,
    harness: Harness,
    relations: tuple,
    expected_output: dict,
) -> None:
    """
    arrange: none
    act: start the flask charm, set flask-app container to be ready and relate it to the db.
    assert: get_uris() should return the correct databaseURI dict
    """
    container: Container = harness.model.unit.get_container(FLASK_CONTAINER_NAME)
    send_signal_mock = unittest.mock.MagicMock()
    monkeypatch.setattr(container, "send_signal", send_signal_mock)

    databases = Databases(unittest.mock.MagicMock())
    assert not databases.get_uris()

    # Create the databases mock with the relation data
    databases = {}
    for relation in relations:
        interface = relation["interface"]
        database_require = unittest.mock.MagicMock()
        database_require.fetch_relation_data = unittest.mock.MagicMock(return_value={"data": relation["data"]})
        database_require.database = relation["data"].get("database", FLASK_DATABASE_NAME)
        databases[interface] = database_require

    # Allowing protected access to test the output
    # pylint: disable=protected-access
    databases._databases = databases

    assert databases.get_uris() == expected_output
