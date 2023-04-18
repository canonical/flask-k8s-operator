# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the GunicornWebserver class to represent the gunicorn server."""
import pathlib
import signal

from charm_state import CharmState


class GunicornWebserver:
    """A class representing a Gunicorn web server."""

    def __init__(self, charm_state: CharmState):
        """Initialize a new instance of the GunicornWebserver class.

        Args:
            charm_state: The state of the charm that the GunicornWebserver instance belongs to.
        """
        self._charm_state = charm_state

    @property
    def config(self) -> str:
        """Generate the content of the Gunicorn configuration file based on charm states.

        Returns:
            The content of the Gunicorn configuration file.
        """
        config_entries = [
            f"bind = ['0.0.0.0:{self._charm_state.flask_port}']",
            f"chdir = {repr(str(self._charm_state.flask_dir.absolute()))}",
        ]
        settings = ("workers", "threads", "keepalive", "timeout")
        for setting in settings:
            setting_value = getattr(self._charm_state.webserver_config, setting)
            if setting_value is None:
                continue
            setting_value = (
                setting_value
                if isinstance(setting_value, int)
                else int(setting_value.total_seconds())
            )
            config_entries.append(f"{setting} = {setting_value}")
        return "\n".join(config_entries)

    @property
    def config_path(self) -> pathlib.Path:
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
            str(self.config_path),
            self._charm_state.flask_wsgi_app_path,
        ]

    @property
    def check_config_command(self) -> list[str]:
        """Returns the command to check the Gunicorn configuration.

        Returns:
            The command to check the Gunicorn configuration.
        """
        return self.command + ["--check-config"]

    @property
    def reload_signal(self) -> signal.Signals:
        """Get the signal used to reload the Gunicorn web server.

        Returns:
            The signal used to reload the Gunicorn web server.
        """
        return signal.SIGHUP
