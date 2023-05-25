# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm database relations unit tests."""

import unittest.mock

import pytest
from ops.model import Container
from ops.testing import Harness

FLASK_CONTAINER_NAME = "flask-app"


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
def test_database_uri(
    monkeypatch: pytest.MonkeyPatch,
    harness: Harness,
    relations: tuple,
    expected_output: dict,
) -> None:
    """
    arrange: none
    act: start the flask charm, set flask-app container to be ready and relate it to the db.
    assert: _database_uri() should return the correct databaseURI dict
    """
    container: Container = harness.model.unit.get_container(FLASK_CONTAINER_NAME)

    send_signal_mock = unittest.mock.MagicMock()
    monkeypatch.setattr(container, "send_signal", send_signal_mock)
    harness.begin()

    # Allowing protected access to test the output
    # pylint: disable=protected-access
    assert harness.charm._databases.get_uris() == {}

    for relation in relations:
        database_charm_name = f"some_db_charm_{relation['interface']}"
        relation_id: int = harness.add_relation(relation["interface"], database_charm_name)
        harness.add_relation_unit(relation_id, f"{database_charm_name}/0")
        harness.update_relation_data(relation_id, database_charm_name, relation["data"])
        harness.update_config()

    # Allowing protected access to test the output
    # pylint: disable=protected-access
    assert harness.charm._databases.get_uris() == expected_output
