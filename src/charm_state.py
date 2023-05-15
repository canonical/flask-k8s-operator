# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""This module defines the CharmState class which represents the state of the Flask charm."""

import datetime
import itertools
import pathlib
import typing

from ops.charm import CharmBase
from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel,
    Extra,
    Field,
    ValidationError,
    validator,
)

from charm_types import WebserverConfig
from consts import KNOWN_CHARM_CONFIG
from exceptions import CharmConfigInvalidError


class FlaskConfig(BaseModel, extra=Extra.allow):  # pylint: disable=too-few-public-methods
    """Represent Flask builtin configuration values.

    Attrs:
        env: what environment the Flask app is running in, by default it's 'production'.
        debug: whether Flask debug mode is enabled.
        secret_key: a secret key that will be used for securely signing the session cookie
            and can be used for any other security related needs by your Flask application.
        permanent_session_lifetime: set the cookie’s expiration to this number of seconds in the
            Flask application permanent sessions.
        application_root: inform the Flask application what path it is mounted under by the
            application / web server.
        session_cookie_secure: set the secure attribute in the Flask application cookies.
        preferred_url_scheme: use this scheme for generating external URLs when not in a request
            context in the Flask application.
    """

    env: str = Field(None, min_length=1)
    debug: bool = Field(None)
    secret_key: str = Field(None, min_length=1)
    permanent_session_lifetime: int = Field(None, gt=0)
    application_root: str = Field(None, min_length=1)
    session_cookie_secure: bool = Field(None)
    preferred_url_scheme: str = Field(None, regex="(?i)^(HTTP|HTTPS)$")

    @validator("preferred_url_scheme")
    @classmethod
    def to_upper(cls, value: str) -> str:
        """Convert the string field to uppercase.

        Args:
            value: the input value.

        Returns:
            The string converted to uppercase.
        """
        return value.upper()


class CharmState:
    """Represents the state of the Flask charm.

    Attrs:
        webserver_config: the web server configuration file content for the charm.
        flask_config: the value of the flask_config charm configuration.
        app_config: user-defined configurations for the Flask application.
        base_dir: the base directory of the Flask application.
        flask_dir: the path to the Flask directory.
        flask_wsgi_app_path: the path to the Flask directory.
        flask_port: the port number to use for the Flask server.
    """

    def __init__(
        self,
        *,
        flask_config: dict[str, int | str] | None = None,
        app_config: dict[str, int | str | bool] | None = None,
        webserver_workers: int | None = None,
        webserver_threads: int | None = None,
        webserver_keepalive: int | None = None,
        webserver_timeout: int | None = None,
    ):
        """Initialize a new instance of the CharmState class.

        Args:
            flask_config: The value of the flask_config charm configuration.
            app_config: User-defined configuration values for the Flask configuration.
            webserver_workers: The number of workers to use for the web server,
                or None if not specified.
            webserver_threads: The number of threads per worker to use for the web server,
                or None if not specified.
            webserver_keepalive: The time to wait for requests on a Keep-Alive connection,
                or None if not specified.
            webserver_timeout: The request silence timeout for the web server,
                or None if not specified.
        """
        self._webserver_workers = webserver_workers
        self._webserver_threads = webserver_threads
        self._webserver_keepalive = webserver_keepalive
        self._webserver_timeout = webserver_timeout
        self._flask_config = flask_config if flask_config is not None else {}
        self._app_config = app_config if app_config is not None else {}

    @classmethod
    def from_charm(cls, charm: CharmBase) -> "CharmState":
        """Initialize a new instance of the CharmState class from the associated charm.

        Args:
            charm: The charm instance associated with this state.

        Return:
            The CharmState instance created by the provided charm.

        Raises:
            CharmConfigInvalidError: if the charm configuration is invalid.
        """
        keepalive = charm.config.get("webserver_keepalive")
        timeout = charm.config.get("webserver_timeout")
        workers = charm.config.get("webserver_workers")
        threads = charm.config.get("webserver_threads")
        flask_config = {
            k.removeprefix("flask_"): v
            for k, v in charm.config.items()
            if k.startswith("flask_") and k in KNOWN_CHARM_CONFIG
        }
        app_config = {
            k.removeprefix("flask_"): v
            for k, v in charm.config.items()
            if k.startswith("flask_") and k not in KNOWN_CHARM_CONFIG
        }
        try:
            valid_flask_config = FlaskConfig(**flask_config)  # type: ignore
        except ValidationError as exc:
            error_fields = set(
                itertools.chain.from_iterable(error["loc"] for error in exc.errors())
            )
            error_field_str = " ".join(f"flask_{f}" for f in error_fields)
            raise CharmConfigInvalidError(f"invalid configuration: {error_field_str}") from exc
        return cls(
            flask_config=valid_flask_config.dict(exclude_unset=True, exclude_none=True),
            app_config=typing.cast(dict[str, str | int | bool], app_config),
            webserver_workers=int(workers) if workers is not None else None,
            webserver_threads=int(threads) if threads is not None else None,
            webserver_keepalive=int(keepalive) if keepalive is not None else None,
            webserver_timeout=int(timeout) if timeout is not None else None,
        )

    @property
    def webserver_config(self) -> WebserverConfig:
        """Get the web server configuration file content for the charm.

        Returns:
            The web server configuration file content for the charm.
        """
        return WebserverConfig(
            workers=self._webserver_workers,
            threads=self._webserver_threads,
            keepalive=datetime.timedelta(seconds=int(self._webserver_keepalive))
            if self._webserver_keepalive is not None
            else None,
            timeout=datetime.timedelta(seconds=int(self._webserver_timeout))
            if self._webserver_timeout is not None
            else None,
        )

    @property
    def flask_config(self) -> dict[str, str | int | bool]:
        """Get the value of the flask_config charm configuration.

        Returns:
            The value of the flask_config charm configuration.
        """
        return self._flask_config.copy()

    @property
    def app_config(self) -> dict[str, str | int | bool]:
        """Get the value of user-defined Flask application configurations.

        Returns:
            The value of user-defined Flask application configurations.
        """
        return self._app_config.copy()

    @property
    def base_dir(self) -> pathlib.Path:
        """Get the base directory of the Flask application.

        Returns:
            The base directory of the Flask application.
        """
        return pathlib.Path("/srv/flask")

    @property
    def flask_dir(self) -> pathlib.Path:
        """Gets the path to the Flask directory.

        Returns:
            The path to the Flask directory.
        """
        return self.base_dir / "app"

    @property
    def flask_wsgi_app_path(self) -> str:
        """Gets the Flask WSGI application in pattern $(MODULE_NAME):$(VARIABLE_NAME).

        The MODULE_NAME should be relative to the flask directory.

        Returns:
            The path to the Flask WSGI application.
        """
        return "app:app"

    @property
    def flask_port(self) -> int:
        """Gets the port number to use for the Flask server.

        Returns:
            The port number to use for the Flask server.
        """
        return 8000
