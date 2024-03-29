#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging
import typing

import ops
from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer

from charm_state import CharmState
from constants import FLASK_CONTAINER_NAME
from database_migration import DatabaseMigration, DatabaseMigrationStatus
from databases import Databases, get_uris, make_database_requirers
from exceptions import CharmConfigInvalidError
from flask_app import FlaskApp
from observability import Observability
from secret_storage import SecretStorage
from webserver import GunicornWebserver

logger = logging.getLogger(__name__)


class FlaskCharm(ops.CharmBase):
    """Flask Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self._secret_storage = SecretStorage(charm=self)
        database_requirers = make_database_requirers(self)

        try:
            self._charm_state = CharmState.from_charm(
                charm=self,
                secret_storage=self._secret_storage,
                database_uris=get_uris(database_requirers),
            )
        except CharmConfigInvalidError as exc:
            self._update_app_and_unit_status(ops.BlockedStatus(exc.msg))
            return

        self._database_migration = DatabaseMigration(
            flask_container=self.unit.get_container(FLASK_CONTAINER_NAME),
            charm_state=self._charm_state,
        )
        webserver = GunicornWebserver(
            charm_state=self._charm_state,
            flask_container=self.unit.get_container(FLASK_CONTAINER_NAME),
        )
        self._flask_app = FlaskApp(
            charm=self,
            charm_state=self._charm_state,
            webserver=webserver,
            database_migration=self._database_migration,
        )
        self._databases = Databases(
            charm=self,
            flask_app=self._flask_app,
            database_requirers=database_requirers,
        )
        self._ingress = IngressPerAppRequirer(
            self,
            port=self._charm_state.flask_port,
            strip_prefix=True,
        )
        self._observability = Observability(charm=self, charm_state=self._charm_state)

        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.rotate_secret_key_action, self._on_rotate_secret_key_action)
        self.framework.observe(
            self.on.secret_storage_relation_changed, self._on_secret_storage_relation_changed
        )
        self.framework.observe(self.on.flask_app_pebble_ready, self._on_flask_app_pebble_ready)

    def _on_config_changed(self, _event: ops.EventBase) -> None:
        """Configure the flask pebble service layer.

        Args:
            _event: the config-changed event that triggers this callback function.
        """
        self._restart_flask()

    def _on_rotate_secret_key_action(self, event: ops.ActionEvent) -> None:
        """Handle the rotate-secret-key action.

        Args:
            event: the action event that trigger this callback.
        """
        if not self.unit.is_leader():
            event.fail("only leader unit can rotate secret key")
            return
        if not self._secret_storage.is_initialized:
            event.fail("flask charm is still initializing")
            return
        self._secret_storage.reset_flask_secret_key()
        event.set_results({"status": "success"})
        self._restart_flask()

    def _on_secret_storage_relation_changed(self, _event: ops.RelationEvent) -> None:
        """Handle the secret-storage-relation-changed event.

        Args:
            _event: the action event that triggers this callback.
        """
        self._restart_flask()

    def _update_app_and_unit_status(self, status: ops.StatusBase) -> None:
        """Update the application and unit status.

        Args:
            status: the desired application and unit status.
        """
        self.unit.status = status
        if self.unit.is_leader():
            self.app.status = status

    def _restart_flask(self) -> None:
        """Restart or start the flask service if not started with the latest configuration."""
        try:
            self._flask_app.restart_flask()
            self._update_app_and_unit_status(ops.ActiveStatus())
        except CharmConfigInvalidError as exc:
            self._update_app_and_unit_status(ops.BlockedStatus(exc.msg))

    def _on_update_status(self, _: ops.HookEvent) -> None:
        """Handle the update-status event."""
        if self._database_migration.get_status() == DatabaseMigrationStatus.FAILED:
            self._restart_flask()

    def _on_flask_app_pebble_ready(self, _: ops.PebbleReadyEvent) -> None:
        """Handle the pebble-ready event."""
        self._restart_flask()


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(FlaskCharm)
