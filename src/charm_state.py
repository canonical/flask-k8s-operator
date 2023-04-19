# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""This module defines the CharmState class which represents the state of the Flask charm."""

import datetime
import pathlib
import typing

from charm_types import FlaskConfig, WebserverConfig


class CharmState:
    """Represents the state of the Flask charm."""

    def __init__(self, charm_config: typing.Mapping[str, str]):
        """Initialize a new instance of the CharmState class.

        Args:
            charm_config: Charm configurations of the charm instance associated with this state.
        """
        self._charm_config = charm_config

    @property
    def webserver_config(self) -> WebserverConfig:
        """Gets the web server configuration file content for the charm.

        Returns:
            The web server configuration file content for the charm.
        """
        keepalive = self._charm_config.get("webserver_keepalive")
        timeout = self._charm_config.get("webserver_timeout")
        workers = self._charm_config.get("webserver_workers")
        threads = self._charm_config.get("webserver_threads")
        return WebserverConfig(
            workers=int(workers) if workers is not None else None,
            threads=int(threads) if threads is not None else None,
            keepalive=datetime.timedelta(seconds=int(keepalive))
            if keepalive is not None
            else None,
            timeout=datetime.timedelta(seconds=int(timeout)) if timeout is not None else None,
        )

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

    @property
    def flask_config(self) -> FlaskConfig:
        """Build a Flask configuration object from the charm configuration.

        Returns:
            A Flask configuration object.
        """
        charm_config = self._charm_config
        return FlaskConfig(
            env=charm_config.get("flask_env"),
            debug=str(charm_config["flask_debug"]).lower() == "true",
            secret_key=charm_config.get("flask_secret_key"),
            permanent_session_lifetime=None
            if charm_config.get("flask_permanent_session_lifetime") is None
            else datetime.timedelta(
                seconds=int(charm_config.get("flask_permanent_session_lifetime", "0"))
            ),
            application_root=charm_config.get("flask_application_root"),
            session_cookie_secure=str(charm_config["flask_session_cookie_secure"]).lower()
            == "true",
            preferred_url_scheme=charm_config.get("flask_preferred_url_scheme"),
        )
