# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm unit tests."""

# pylint: disable=protected-access

from ops.testing import Harness
import pytest

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
        "startup": "enabled",
        "environment": {"FLASK_DATABASE_URI": ""},
    }


@pytest.mark.parametrize(
    "relation_data, expected_output",
    [
        (
            {
                "endpoints": "test-mysql:3306",
                "password": "test-password",
                "username": "test-username",
            },
            "mysql://test-username:test-password@test-mysql:3306/flask-app",
        ),
        (
            {
                "database": "test-database",
                "endpoints": "test-mysql:3306,test-mysql-2:3306",
                "password": "test-password",
                "username": "test-username",
            },
            "mysql://test-username:test-password@test-mysql:3306/test-database",
        ),
    ],
)
def test_database_uri(
    harness: Harness,
    relation_data,
    expected_output,
) -> None:
    """
    arrange: none
    act: start the flask charm, set flask-app container to be ready and relate it to the db.
    assert: _database_uri() should return the correct databaseURI
    """
    harness.begin_with_initial_hooks()
    harness.container_pebble_ready("flask-app")
    assert harness.charm._database_uri() == ""

    mysql_relation_id: int = harness.add_relation("mysql", "mysql-k8s")

    harness.update_relation_data(mysql_relation_id, "mysql-k8s", relation_data)
    assert harness.charm._database_uri() == expected_output
