# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Exceptions used by the Flask charm."""


class WebserverConfigInvalid(Exception):
    """
    Exception raised when a webserver configuration is found to be invalid.

    Attrs:
        msg (str): Explanation of the error.
    """

    def __init__(self, msg):
        """
        Initializes a new instance of the WebserverConfigInvalid exception.

        Args:
            msg (str): Explanation of the error.
        """
        self.msg = msg
