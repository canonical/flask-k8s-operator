#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging

from ops.charm import CharmBase
from ops.main import main

logger = logging.getLogger(__name__)


class FlaskCharm(CharmBase):
    """Flask Charm service."""


if __name__ == "__main__":  # pragma: nocover
    main(FlaskCharm)
