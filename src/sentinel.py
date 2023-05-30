# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Utilities for identifying the use of sentinel image in Flask-K8s charm deployment.

The Flask-K8s charm operates under a 'Bring Your Own Container Image' mode, requiring users
to supply a container image for their Flask application. However, to fulfill CharmHub's
requirements, a sentinel image is provided as a placeholder.

Functions in this module assist in determining if the Flask application container image
deployed is the sentinel image. If so, the charm can trigger a user-friendly error message.
"""

from ops import CharmBase

from constants import FLASK_CONTAINER_NAME


class Sentinel:  # pylint: disable=too-few-public-methods
    """A helper class for checking if the deployed Flask application image is a sentinel image."""

    def __init__(self, charm: CharmBase):
        """Initialize the Sentinel object.

        Args:
            charm: associated charm object.
        """
        self._charm = charm

    def is_sentinel_image(self) -> bool:
        """Check if the Flask application container is using the sentinel image.

        Returns: True if the sentinel image is being used, False otherwise.
        """
        container = self._charm.unit.get_container(FLASK_CONTAINER_NAME)
        if container.can_connect():
            return container.exists("/null")
        return False
