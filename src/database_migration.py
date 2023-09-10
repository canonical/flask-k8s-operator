# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the DatabaseMigration class to manage database migrations."""

import logging
from typing import Literal, cast

import ops
from ops.pebble import ExecError

from charm_state import CharmState
from constants import FLASK_STATE_DIR
from exceptions import CharmConfigInvalidError

logger = logging.getLogger(__name__)


DatabaseMigrationStatus = Literal["PENDING", "COMPLETED", "FAILED"]


class DatabaseMigration:
    """The DatabaseMigration class that manages database migrations.

    Attrs:
        script: the database migration script.
        COMPLETED: one of the possible database migration status.
        FAILED: one of the possible database migration status.
        PENDING: one of the possible database migration status.
    """

    _STATUS_FILE = FLASK_STATE_DIR / "database-migration-status"
    _COMPLETED_SCRIPT_FILE = FLASK_STATE_DIR / "completed-database-migration"

    COMPLETED: DatabaseMigrationStatus = "COMPLETED"
    FAILED: DatabaseMigrationStatus = "FAILED"
    PENDING: DatabaseMigrationStatus = "PENDING"

    def __init__(self, flask_container: ops.Container, charm_state: CharmState):
        """Initialize the DatabaseMigration instance.

        Args:
            flask_container: The flask container object.
            charm_state: The charm state.
        """
        self._container = flask_container
        self._charm_state = charm_state

    @property
    def script(self) -> str | None:
        """Get the database migration script."""
        return self._charm_state.database_migration_script

    def get_status(self) -> DatabaseMigrationStatus:
        """Get the database migration run status.

        Returns:
            One of "PENDING", "COMPLETED", or "FAILED".
        """
        return cast(
            DatabaseMigrationStatus,
            self.PENDING
            if not self._container.exists(self._STATUS_FILE)
            else self._container.pull(self._STATUS_FILE).read(),
        )

    def _set_status(self, status: DatabaseMigrationStatus) -> None:
        """Set the database migration run status.

        Args:
            status: One of "PENDING", "COMPLETED", or "FAILED".
        """
        self._container.make_dir(self._STATUS_FILE.parent, make_parents=True)
        self._container.push(self._STATUS_FILE, source=status)

    def get_completed_script(self) -> str | None:
        """Get the database migration script that has completed in the current container.

        Returns:
            The completed database migration script in the current container.
        """
        if self._container.exists(self._COMPLETED_SCRIPT_FILE):
            return cast(str, self._container.pull(self._COMPLETED_SCRIPT_FILE).read())
        return None

    def _set_completed_script(self, script_path: str) -> None:
        """Set the database migration script that has completed in the current container.

        Args:
            script_path: The completed database migration script in the current container.
        """
        self._container.make_dir(self._COMPLETED_SCRIPT_FILE.parent, make_parents=True)
        self._container.push(self._COMPLETED_SCRIPT_FILE, script_path)

    def run(self, environment: dict[str, str]) -> None:
        """Run the database migration script if database migration is still pending.

        Args:
            environment: Environment variables that's required for the run.

        Raises:
            CharmConfigInvalidError: if the database migration run failed.
        """
        if self.get_status() in (self.PENDING, self.FAILED) and self.script:
            logger.info("execute database migration script: %s", repr(self.script))
            try:
                self._container.exec(
                    ["/bin/bash", "-xeo", "pipefail", self.script],
                    environment=environment,
                    working_dir="/srv/flask/app",
                ).wait()
                self._set_status(self.COMPLETED)
                self._set_completed_script(self.script)
            except ExecError as exc:
                self._set_status(self.FAILED)
                logger.error(
                    "database migration script %s failed, stdout: %s, stderr: %s",
                    repr(self.script),
                    exc.stdout,
                    exc.stderr,
                )
                raise CharmConfigInvalidError(
                    f"database migration script {self.script!r} failed, "
                    "will retry in next update-status"
                ) from exc
