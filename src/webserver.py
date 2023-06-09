# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the GunicornWebserver class to represent the gunicorn server."""
import datetime
import logging
import pathlib
import signal
import typing

import ops
from ops.pebble import ExecError, PathError

from charm_state import CharmState
from constants import FLASK_SERVICE_NAME
from exceptions import CharmConfigInvalidError
from flask_app import FlaskApp

logger = logging.getLogger(__name__)


class GunicornWebserver:
    """A class representing a Gunicorn web server.

    Attrs:
        command: the command to start the Gunicorn web server.

    """

    def __init__(
        self, charm_state: CharmState, flask_container: ops.Container, flask_app: FlaskApp
    ):
        """Initialize a new instance of the GunicornWebserver class.

        Args:
            charm_state: The state of the charm that the GunicornWebserver instance belongs to.
            flask_container: The Flask container in this charm unit.
            flask_app: The Flask application instance.
        """
        self._charm_state = charm_state
        self._flask_container = flask_container
        self._flask_app = flask_app

    @property
    def _config(self) -> str:
        """Generate the content of the Gunicorn configuration file based on charm states.

        Returns:
            The content of the Gunicorn configuration file.
        """
        config_entries = []
        for setting, setting_value in self._charm_state.webserver_config.items():
            setting_value = typing.cast(None | int | datetime.timedelta, setting_value)
            if setting_value is None:
                continue
            setting_value = (
                setting_value
                if isinstance(setting_value, int)
                else int(setting_value.total_seconds())
            )
            config_entries.append(f"{setting} = {setting_value}")
        new_line = "\n"
        config = f"""\
bind = ['0.0.0.0:{self._charm_state.flask_port}']
chdir = {repr(str(self._charm_state.flask_dir.absolute()))}
accesslog = {repr(str(self._charm_state.flask_access_log.absolute()))}
errorlog = {repr(str(self._charm_state.flask_error_log.absolute()))}
statsd_host = {repr(self._charm_state.flask_statsd_host)}
{new_line.join(config_entries)}"""
        return config

    @property
    def _config_path(self) -> pathlib.Path:
        """Gets the path to the Gunicorn configuration file.

        Returns:
            The path to the web server configuration file.
        """
        return self._charm_state.base_dir / "gunicorn.conf.py"

    @property
    def command(self) -> list[str]:
        """Get the command to start the Gunicorn web server.

        Returns:
            The command to start the Gunicorn web server.
        """
        return [
            "python3",
            "-m",
            "gunicorn",
            "-c",
            str(self._config_path),
            self._charm_state.flask_wsgi_app_path,
        ]

    @property
    def _check_config_command(self) -> list[str]:
        """Returns the command to check the Gunicorn configuration.

        Returns:
            The command to check the Gunicorn configuration.
        """
        return self.command + ["--check-config"]

    @property
    def _reload_signal(self) -> signal.Signals:
        """Get the signal used to reload the Gunicorn web server.

        Returns:
            The signal used to reload the Gunicorn web server.
        """
        return signal.SIGHUP

    def _check_config(self) -> None:
        """Execute a command to validate the flask configuration in the container.

        Raises:
            CharmConfigInvalidError: If the web server configuration check fails.
        """
        container = self._flask_container
        exec_process = container.exec(
            self._check_config_command, environment=self._flask_app.flask_environment()
        )
        try:
            exec_process.wait_output()
        except ExecError as exc:
            logger.error(
                "webserver configuration check failed, stdout: %s, stderr: %s",
                exc.stdout,
                exc.stderr,
            )
            raise CharmConfigInvalidError(
                "Webserver configuration check failed, please review your charm configuration"
            ) from exc

    def update_config(self, is_webserver_running: bool) -> None:
        """Update and apply the configuration file of the web server.

        Args:
            is_webserver_running: Indicates if the web server container is currently running.
        """
        self._prepare_flask_log_dir()
        webserver_config_path = str(self._config_path)
        try:
            current_webserver_config = self._flask_container.pull(webserver_config_path)
        except PathError:
            current_webserver_config = None
        self._flask_container.push(webserver_config_path, self._config)
        if current_webserver_config == self._config:
            return
        self._check_config()
        if is_webserver_running:
            logger.info("gunicorn config changed, reloading")
            self._flask_container.send_signal(self._reload_signal, FLASK_SERVICE_NAME)

    def _prepare_flask_log_dir(self) -> None:
        """Prepare Flask access and error log directory for the Flask application."""
        container = self._flask_container
        for log in (self._charm_state.flask_access_log, self._charm_state.flask_error_log):
            log_dir = str(log.parent.absolute())
            if not container.isdir(log_dir):
                container.make_dir(log_dir, make_parents=True)
