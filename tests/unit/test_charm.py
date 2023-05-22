# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm unit tests."""

# pylint: disable=protected-access

import unittest.mock

import pytest
from ops.model import ActiveStatus, Container

import yaml
from ops.testing import Harness

from consts import FLASK_CONTAINER_NAME
from charm_state import KNOWN_CHARM_CONFIG

FLASK_BASE_DIR = "/srv/flask"


def test_flask_pebble_layer(harness: Harness) -> None:
    """
    arrange: none
    act: start the flask charm and set flask-app container to be ready.
    assert: flask charm should submit the correct flaks pebble layer to pebble.
    """
    harness.begin_with_initial_hooks()
    harness.set_can_connect(harness.model.unit.containers["flask-app"], True)
    harness.framework.reemit()
    flask_layer = harness.get_container_pebble_plan("flask-app").to_dict()["services"]["flask-app"]
    assert flask_layer == {
        "override": "replace",
        "summary": "Flask application service",
        "command": f"python3 -m gunicorn -c {FLASK_BASE_DIR}/gunicorn.conf.py app:app",
        "environment": {"FLASK_PREFERRED_URL_SCHEME": "HTTPS"},
        "startup": "enabled",
    }


@pytest.mark.parametrize(
    "relations, expected_output",
    [
        (
            (
                {
                    "interface": "mysql",
                    "data": {
                        "endpoints": "test-mysql:3306",
                        "password": "test-password",
                        "username": "test-username",
                    },
                },
            ),
            {
                "mysql": "mysql://test-username:test-password@test-mysql:3306/flask-app",
            },
        ),
        (
            (
                {
                    "interface": "postgresql",
                    "data": {
                        "database": "test-database",
                        "endpoints": "test-postgresql:5432,test-postgresql-2:5432",
                        "password": "test-password",
                        "username": "test-username",
                    },
                },
            ),
            {
                "postgresql": (
                    "postgresql://test-username:test-password"
                    "@test-postgresql:5432/test-database"
                )
            },
        ),
        (
            (
                {
                    "interface": "mysql",
                    "data": {
                        "endpoints": "test-mysql:3306",
                        "password": "test-password",
                        "username": "test-username",
                    },
                },
                {
                    "interface": "postgresql",
                    "data": {
                        "database": "test-database",
                        "endpoints": "test-postgresql:5432,test-postgresql-2:5432",
                        "password": "test-password",
                        "username": "test-username",
                    },
                },
            ),
            {
                "mysql": "mysql://test-username:test-password@test-mysql:3306/flask-app",
                "postgresql": (
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

    harness.begin_with_initial_hooks()
    harness.set_can_connect(harness.model.unit.containers["flask-app"], True)
    assert isinstance(harness.model.unit.status, ActiveStatus)
    assert harness.charm._database_uri() == {}

    for relation in relations:
        print(relation)
        database_charm_name = f"some_db_charm_{relation['interface']}"
        relation_id: int = harness.add_relation(relation["interface"], database_charm_name)
        harness.add_relation_unit(relation_id, f"{database_charm_name}/0")
        harness.update_relation_data(relation_id, database_charm_name, relation["data"])

    assert harness.charm._database_uri() == expected_output


def test_known_charm_config():
    """
    arrange: none
    act: none
    assert: KNOWN_CHARM_CONFIG in the consts module matches the content of config.yaml file.
    """
    with open("config.yaml", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    assert sorted(config["options"].keys()) == sorted(KNOWN_CHARM_CONFIG)
