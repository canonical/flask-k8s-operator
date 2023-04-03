# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""pytest fixtures for the integration test."""

import ops.testing
import pytest

from charm import FlaskCharm


@pytest.fixture(name="harness")
def harness_fixture():
    """Ops testing framework harness fixture."""
    ops.testing.SIMULATE_CAN_CONNECT = True
    harness = ops.testing.Harness(FlaskCharm)

    yield harness

    harness.cleanup()
    ops.testing.SIMULATE_CAN_CONNECT = False
