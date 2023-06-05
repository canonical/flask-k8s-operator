# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Exceptions used by the Flask charm."""


class CharmConfigInvalidError(Exception):
    """Exception raised when a charm configuration is found to be invalid.

    Attrs:
        msg (str): Explanation of the error.
    """

    def __init__(self, msg: str):
        """Initialize a new instance of the CharmConfigInvalidError exception.

        Args:
            msg (str): Explanation of the error.
        """
        self.msg = msg


class PebbleNotReadyError(Exception):
    """Exception raised when accessing pebble while it isn't ready."""


class InvalidDatabaseRelationDataError(Exception):
    """Exception raised when the relation data with a database is not valid.

    Attrs:
        msg (str): Explanation of the error.
    """

    def __init__(self, msg: str):
        """Initialize a new instance of the InvalidDatabaseRelationDataError exception.

        Args:
            msg (str): Explanation of the error.
        """
        self.msg = msg
