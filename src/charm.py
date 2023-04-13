#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging
import signal
import typing

from ops.charm import CharmBase, ConfigChangedEvent
from ops.main import main
from ops.model import ActiveStatus, Container
from ops.pebble import PathError

logger = logging.getLogger(__name__)


class FlaskCharm(CharmBase):
    """Flask Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self.config_service)

    def flask_container(self, require_connected: bool = True) -> Container:
        """Get the flask application workload container controller.

        Args:
            require_connected: if set to ``True``, a runtime exception will be raised if the
                pebble inside the container is not ready.

        Return:
            The controller of the flask application workload container.

        Raises:
            RuntimeError: if the pebble inside  the container is not ready while the
                ``require_connected`` is set to True.
        """
        container = self.unit.get_container("flask-app")
        if require_connected and not container.can_connect():
            raise RuntimeError("pebble inside flask-app container is not ready")
        return container

    def config_service(self, event: ConfigChangedEvent) -> None:
        """Configure the flask pebble service layer.

        Args:
            event: the config-changed event that trigger this callback function.
        """
        container = self.flask_container(require_connected=False)
        if not container.can_connect():
            event.defer()
            return
        service_name = "flask-app"
        gunicorn_config_path = "/srv/flask/gunicorn.conf.py"
        current_gunicorn_config = self.pull_file(gunicorn_config_path)
        gunicorn_config = self.gunicorn_config()
        self.push_file(gunicorn_config_path, gunicorn_config)
        container.add_layer("flask-app", self.flask_layer(), combine=True)
        current_running = container.get_service(service_name).is_running()
        if current_gunicorn_config != gunicorn_config and current_running:
            logger.info("gunicorn config changed, reloading")
            container.send_signal(signal.SIGHUP, service_name)
        container.replan()
        self.unit.status = ActiveStatus()

    def push_file(self, path: str, content: str) -> None:
        """Write the given text content to a file inside the workload container.

        If the file doesn't exist, a new file will be created. All pre-existent content will be
        overwritten by this operation.

        Args:
            path: Path to the file in the workload container.
            content: the text content to be written to the file.
        """
        self.flask_container().push(path, content, encoding="utf-8")

    def pull_file(self, path: str) -> str | None:
        """Retrieve the content of the given file from the flask workload container.

        Args:
            path: Path to the file in the workload container.

        Returns:
            The content of the given file in the flask workload container, ``None`` if the file
            doesn't exist.
        """
        try:
            return typing.cast(str, self.flask_container().pull(path).read())
        except PathError:
            return None

    def gunicorn_config(self) -> str:
        """Generate the content of the gunicorn configuration file based on charm configurations.

        Returns:
            The content of the gunicorn configuration file.
        """
        config_entries = ["bind = ['0.0.0.0:8000']", "chdir = '/srv/flask/app'"]
        settings = ("workers", "threads", "keepalive", "timeout")
        for setting in settings:
            config_name = f"webserver_{setting}"
            if self.config.get(config_name) is not None:
                config_entries.append(f"{setting} = {self.config.get(config_name)}")
        return "\n".join(config_entries)

    def flask_layer(self) -> dict:
        """Generate the pebble layer definition for flask application.

        Returns:
            The pebble layer definition for flask application.
        """
        return {
            "services": {
                "flask-app": {
                    "override": "replace",
                    "summary": "Flask application service",
                    "command": "python3 -m gunicorn -c /srv/flask/gunicorn.conf.py app:app",
                    "user": "flask",
                    "group": "flask",
                    "startup": "enabled",
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    main(FlaskCharm)
