#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Type definitions for the Flask charm."""

import datetime
import typing


class WebserverConfig(typing.NamedTuple):
    """Represent the configuration values for a web server.

    Attributes:
        workers: The number of workers to use for the web server, or None if not specified.
        threads: The number of threads per worker to use for the web server,
            or None if not specified.
        keepalive: The time to wait for requests on a Keep-Alive connection,
            or None if not specified.
        timeout: The request silence timeout for the web server, or None if not specified.
    """

    workers: int | None
    threads: int | None
    keepalive: datetime.timedelta | None
    timeout: datetime.timedelta | None


class ExecResult(typing.NamedTuple):
    """A named tuple representing the result of executing a command.

    Attributes:
        exit_code: The exit status of the command (0 for success, non-zero for failure).
        stdout: The standard output of the command as a string.
        stderr: The standard error output of the command as a string.
    """

    exit_code: int
    stdout: str
    stderr: str
