# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""pytest fixtures for the integration test."""

# pylint: disable=protected-access,too-few-public-methods

import typing
import unittest.mock

import ops
import pytest
from ops.testing import Harness

from charm import FlaskCharm
from constants import FLASK_CONTAINER_NAME
from database_migration import DatabaseMigrationStatus


@pytest.fixture(name="harness")
def harness_fixture() -> typing.Generator[Harness, None, None]:
    """Ops testing framework harness fixture."""
    harness = Harness(FlaskCharm)
    harness.set_leader()
    root = harness.get_filesystem_root(FLASK_CONTAINER_NAME)
    (root / "flask/app").mkdir(parents=True)
    harness.set_can_connect(FLASK_CONTAINER_NAME, True)

    def check_config_handler(_):
        """Handle the gunicorn check config command."""
        config_file = root / "flask/gunicorn.conf.py"
        if config_file.is_file():
            return ops.testing.ExecResult(0)
        return ops.testing.ExecResult(1)

    harness.handle_exec(
        FLASK_CONTAINER_NAME,
        [
            "python3",
            "-m",
            "gunicorn",
            "-c",
            "/flask/gunicorn.conf.py",
            "app:app",
            "--check-config",
        ],
        handler=check_config_handler,
    )

    yield harness
    harness.cleanup()


@pytest.fixture
def database_migration_mock():
    """Create a mock instance for the DatabaseMigration class."""
    mock = unittest.mock.MagicMock()
    mock.status = DatabaseMigrationStatus.PENDING
    mock.script = None
    return mock
