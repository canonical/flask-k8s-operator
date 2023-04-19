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


class FlaskConfig(typing.NamedTuple):
    """Represent the configuration values for a Flask application.

    Attributes:
        env: This corresponds to the Flask ENV configuration value.
        debug: This corresponds to the Flask DEBUG configuration value.
        secret_key: This corresponds to the Flask SECRET_KEY configuration value.
        permanent_session_lifetime: This corresponds to the Flask PERMANENT_SESSION_LIFETIME
            configuration value.
        application_root: This corresponds to the Flask APPLICATION_ROOT configuration value.
        session_cookie_secure: This corresponds to the Flask SESSION_COOKIE_SECURE
            configuration value.
        preferred_url_scheme: This corresponds to the Flask PREFERRED_URL_SCHEME
            configuration value.
    """

    env: str | None
    debug: bool
    secret_key: str | None
    permanent_session_lifetime: datetime.timedelta | None
    application_root: str | None
    session_cookie_secure: bool
    preferred_url_scheme: str | None


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
