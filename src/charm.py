#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging
import typing

import ops
import xiilib.flask.charm

logger = logging.getLogger(__name__)


class FlaskCharm(xiilib.flask.charm.FlaskCharm):
    """Flask Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.rotate_secret_key_action, self._on_rotate_secret_key_action)
        self.framework.observe(
            self.on.secret_storage_relation_changed, self._on_secret_storage_relation_changed
        )
        self.framework.observe(self.on.flask_app_pebble_ready, self._on_flask_app_pebble_ready)
        self.framework.observe(self.on.update_status, self._on_update_status)

    def _on_config_changed(self, event: ops.EventBase) -> None:
        """Configure the flask pebble service layer.

        Args:
            event: the config-changed event that triggers this callback function.
        """
        self.on_config_changed(event)

    def _on_rotate_secret_key_action(self, event: ops.ActionEvent) -> None:
        """Handle the rotate-secret-key action.

        Args:
            event: the action event that trigger this callback.
        """
        self.on_rotate_secret_key_action(event)

    def _on_secret_storage_relation_changed(self, event: ops.RelationEvent) -> None:
        """Handle the secret-storage-relation-changed event.

        Args:
            event: the action event that triggers this callback.
        """
        self.on_secret_storage_relation_changed(event)

    def _on_update_status(self, event: ops.HookEvent) -> None:
        """Handle the update-status event.

        Args:
            event: the action event that triggers this callback.
        """
        self.on_update_status(event)

    def _on_flask_app_pebble_ready(self, event: ops.PebbleReadyEvent) -> None:
        """Handle the pebble-ready event.

        Args:
            event: the action event that triggers this callback.
        """
        self.on_flask_app_pebble_ready(event)


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(FlaskCharm)
