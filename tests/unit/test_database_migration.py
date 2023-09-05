# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for Flask charm database integration."""

import ops
import pytest
from ops.testing import Harness

from charm_state import CharmState
from constants import FLASK_CONTAINER_NAME
from database_migration import DatabaseMigration
from exceptions import CharmConfigInvalidError
from flask_app import FlaskApp
from webserver import GunicornWebserver


def test_database_migration(harness: Harness):
    """
    arrange: none
    act: set the database migration script to be different value.
    assert: the restart_flask method will not invoke the database migration script after the
        first successful run.
    """
    harness.begin()
    container: ops.Container = harness.model.unit.get_container(FLASK_CONTAINER_NAME)
    root = harness.get_filesystem_root(FLASK_CONTAINER_NAME)
    harness.set_can_connect(FLASK_CONTAINER_NAME, True)
    charm_state = CharmState(
        flask_secret_key="abc",
        is_secret_storage_ready=True,
    )
    database_migration = DatabaseMigration(
        flask_container=container, database_migration_script="database-migration.sh"
    )
    webserver = GunicornWebserver(
        charm_state=charm_state,
        flask_container=container,
        database_migration=database_migration,
    )
    flask_app = FlaskApp(charm=harness.charm, charm_state=charm_state, webserver=webserver)
    database_migration_history = []

    def handle_database_migration(args: ops.testing.ExecArgs):
        """Handle the database migration command."""
        script = args.command[-1]
        database_migration_history.append(script)
        if (root / "srv/flask/app" / script).exists():
            return ops.testing.ExecResult(0)
        return ops.testing.ExecResult(1)

    harness.handle_exec(
        FLASK_CONTAINER_NAME, ["/bin/bash", "-xeo", "pipefail"], handler=handle_database_migration
    )
    with pytest.raises(CharmConfigInvalidError):
        flask_app.restart_flask()
    assert database_migration_history == ["database-migration.sh"]

    (root / "srv/flask/app" / "database-migration.sh").touch()
    flask_app.restart_flask()
    assert database_migration_history == ["database-migration.sh"] * 2

    database_migration._script = "database-migration-2.sh"  # pylint: disable=protected-access
    flask_app = FlaskApp(charm=harness.charm, charm_state=charm_state, webserver=webserver)
    with pytest.raises(CharmConfigInvalidError):
        flask_app.restart_flask()
    assert database_migration_history == ["database-migration.sh"] * 2


def test_database_migration_rerun(harness: Harness):
    """
    arrange: none
    act: fail the first database migration run and rerun database migration.
    assert: the second database migration run should be successfully.
    """
    harness.begin()
    container: ops.Container = harness.model.unit.get_container(FLASK_CONTAINER_NAME)
    harness.set_can_connect(FLASK_CONTAINER_NAME, True)
    charm_state = CharmState(
        flask_secret_key="abc",
        is_secret_storage_ready=True,
    )
    database_migration = DatabaseMigration(
        flask_container=container, database_migration_script="database-migration.sh"
    )
    webserver = GunicornWebserver(
        charm_state=charm_state,
        flask_container=container,
        database_migration=database_migration,
    )
    flask_app = FlaskApp(charm=harness.charm, charm_state=charm_state, webserver=webserver)
    harness.handle_exec(FLASK_CONTAINER_NAME, ["/bin/bash", "-xeo", "pipefail"], result=1)
    with pytest.raises(CharmConfigInvalidError):
        flask_app.restart_flask()
    assert database_migration.get_status() == database_migration.FAILED
    harness.handle_exec(FLASK_CONTAINER_NAME, ["/bin/bash", "-xeo", "pipefail"], result=0)
    flask_app.restart_flask()
    assert database_migration.get_status() == database_migration.COMPLETED
