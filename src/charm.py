#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging
import typing

import ops
import xiilib.flask

logger = logging.getLogger(__name__)


class FlaskCharm(xiilib.flask.Charm):
    """Flask Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        if not self.okay:
            return
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        for event_name, event_source in self.supported_events.items():
            self.framework.observe(event_source, getattr(self, f"_on_{event_name}"))


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(FlaskCharm)
