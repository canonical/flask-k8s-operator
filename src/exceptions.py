# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Exceptions used by the Flask charm."""

from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus


class ChangeStatusException(Exception):
    """Exceptions raised when attempting to change the status of a charm unit.

    Attrs:
        status: The status that was attempted to be set.
    """

    def __init__(self, status: ActiveStatus | BlockedStatus | MaintenanceStatus):
        """Initializes a new instance of the ChangeStatusException class.

        Args:
            status: The status that was attempted to be set.
        """
        self.status = status

    def __repr__(self) -> str:
        """Returns a string representation of the ChangeStatusException instance.

        Returns:
            A string representation of the ChangeStatusException instance.
        """
        return f"ChangeStatusException(status={repr(self.status)}"
