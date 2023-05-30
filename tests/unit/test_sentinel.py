# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm unit tests for the sentinel module."""
from ops.testing import Harness

from constants import FLASK_CONTAINER_NAME
from sentinel import Sentinel


def test_sentinel(harness: Harness):
    """
    arrange: start the harness.
    act: create a /null file in the flask-app container.
    assert: sentinel check should return True after the file was added.
    """
    harness.begin()
    sentinel = Sentinel(charm=harness.charm)
    assert not sentinel.is_sentinel_image()
    harness.model.unit.get_container(FLASK_CONTAINER_NAME).push("/null", "")
    assert sentinel.is_sentinel_image()
