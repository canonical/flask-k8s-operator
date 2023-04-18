#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging
import shlex
import typing

from ops.charm import CharmBase, ConfigChangedEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, Container
from ops.pebble import ExecError, PathError

from charm_state import CharmState
from charm_types import ExecResult
from webserver import GunicornWebserver

logger = logging.getLogger(__name__)


class FlaskCharm(CharmBase):
    """Flask Charm service."""

    _FLASK_CONTAINER_NAME = "flask-app"

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self._charm_state = CharmState(charm_config=self.config)
        self._webserver = GunicornWebserver(charm_state=self._charm_state)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def container_can_connect(self) -> bool:
        """Check if the Flask pebble service is connectable.

        Returns:
            True if the Flask pebble service is connectable, False otherwise.
        """
        return self.unit.get_container(self._FLASK_CONTAINER_NAME).can_connect()

    def container(self) -> Container:
        """Get the flask application workload container controller.

        Return:
            The controller of the flask application workload container.

        Raises:
            RuntimeError: if the pebble service inside the container is not ready while the
                ``require_connected`` is set to True.
        """
        if not self.container_can_connect():
            raise RuntimeError("pebble inside flask-app container is not ready")

        container = self.unit.get_container(self._FLASK_CONTAINER_NAME)
        return container

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        """Configure the flask pebble service layer.

        Args:
            event: the config-changed event that trigger this callback function.
        """
        if not self.container_can_connect():
            event.defer()
            return

        container = self.container()
        service_name = "flask-app"
        container.add_layer("flask-app", self.flask_layer(), combine=True)
        webserver_config_path = str(self._webserver.config_path)
        current_webserver_config = self.pull_file(webserver_config_path)
        is_webserver_running = container.get_service(service_name).is_running()
        self.push_file(webserver_config_path, self._webserver.config)
        config_check_result = self.exec(self._webserver.check_config_command)
        if config_check_result.exit_code:
            logger.error(
                "webserver configuration check failed, stdout: %s, stderr: %s",
                config_check_result.stdout,
                config_check_result.stderr
            )
            self.unit.status = BlockedStatus(
                "Webserver configuration check failed, please review your charm configuration"
            )
            return
        if current_webserver_config != self._webserver.config and is_webserver_running:
            logger.info("gunicorn config changed, reloading")
            container.send_signal(self._webserver.reload_signal, service_name)
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
        self.container().push(path, content, encoding="utf-8")

    def pull_file(self, path: str) -> str | None:
        """Retrieve the content of the given file from the flask workload container.

        Args:
            path: Path to the file in the workload container.

        Returns:
            The content of the given file in the flask workload container, ``None`` if the file
            doesn't exist.
        """
        try:
            return typing.cast(str, self.container().pull(path).read())
        except PathError:
            return None

    def exec(self, command: list[str]) -> ExecResult:
        """Execute a command inside the Flask workload container.

        The command will be executed with user flask group flask inside the container.

        Args:
            command: A list of strings representing the command to be executed.

        Returns:
            ExecResult: An `ExecResult` object representing the result of the command execution.
        """
        container = self.container()
        exec_process = container.exec(command, user="flask", group="flask")
        try:
            stdout, stderr = exec_process.wait_output()
            return ExecResult(0, typing.cast(str, stdout), typing.cast(str, stderr))
        except ExecError as exc:
            return ExecResult(
                exc.exit_code, typing.cast(str, exc.stdout), typing.cast(str, exc.stderr)
            )

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
                    "command": shlex.join(self._webserver.command),
                    "user": "flask",
                    "group": "flask",
                    "startup": "enabled",
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    main(FlaskCharm)
