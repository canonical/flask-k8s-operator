# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""This module defines the CharmState class which represents the state of the Flask charm."""

import datetime
import pathlib

from ops.charm import CharmBase

from charm_types import WebserverConfig


class CharmState:
    """Represents the state of the Flask charm."""

    def __init__(
        self,
        webserver_workers: int | None = None,
        webserver_threads: int | None = None,
        webserver_keepalive: int | None = None,
        webserver_timeout: int | None = None,
    ):
        """Initialize a new instance of the CharmState class.

        Args:
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

    @classmethod
    def from_charm(cls, charm: CharmBase) -> "CharmState":
        """Initialize a new instance of the CharmState class from the associated charm.

        Args:
            charm: The charm instance associated with this state.

        Return:
            The CharmState instance created by the provided charm.
        """
        keepalive = charm.config.get("webserver_keepalive")
        timeout = charm.config.get("webserver_timeout")
        workers = charm.config.get("webserver_workers")
        threads = charm.config.get("webserver_threads")
        return cls(
            webserver_workers=int(workers) if workers is not None else None,
            webserver_threads=int(threads) if threads is not None else None,
            webserver_keepalive=int(keepalive) if keepalive is not None else None,
            webserver_timeout=int(timeout) if timeout is not None else None,
        )

    @property
    def webserver_config(self) -> WebserverConfig:
        """Gets the web server configuration file content for the charm.

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
