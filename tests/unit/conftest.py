# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""pytest fixtures for the integration test."""

# pylint: disable=protected-access,too-few-public-methods

import typing

import pytest
from ops.model import Container
from ops.pebble import ExecError
from ops.testing import Harness

from charm import FlaskCharm
from charm_types import ExecResult
from consts import FLASK_CONTAINER_NAME


def inject_register_command_handler(monkeypatch: pytest.MonkeyPatch, harness: Harness):
    """A helper function for injecting an implementation of the register_command_handler method."""
    handler_table: dict[str, typing.Callable[[list[str]], tuple[int, str, str]]] = {}

    class ExecProcessStub:
        """A mock object that simulates the execution of a process in the container."""

        def __init__(self, command: list[str], exit_code: int, stdout: str, stderr: str):
            """Initialize the ExecProcessStub object."""
            self._command = command
            self._exit_code = exit_code
            self._stdout = stdout
            self._stderr = stderr

        def wait_output(self):
            """Simulate the wait_output method of the container object."""
            if self._exit_code == 0:
                return self._stdout, self._stderr
            raise ExecError(
                command=self._command,
                exit_code=self._exit_code,
                stdout=self._stdout,
                stderr=self._stderr,
            )

    def exec_stub(command: list[str], **_kwargs):
        """A mock implementation of the `exec` method of the container object."""
        executable = command[0]
        handler = handler_table[executable]
        exit_code, stdout, stderr = handler(command)
        return ExecProcessStub(command=command, exit_code=exit_code, stdout=stdout, stderr=stderr)

    def register_command_handler(
        container: Container | str,
        executable: str,
        handler=typing.Callable[[list[str]], typing.Tuple[int, str, str]],
    ):
        """Registers a handler for a specific executable command."""
        container = (
            harness.model.unit.get_container(container)
            if isinstance(container, str)
            else container
        )
        handler_table[executable] = handler
        monkeypatch.setattr(container, "exec", exec_stub)

    monkeypatch.setattr(
        harness, "register_command_handler", register_command_handler, raising=False
    )


@pytest.fixture(name="harness")
def harness_fixture(monkeypatch) -> typing.Generator[Harness, None, None]:
    """Ops testing framework harness fixture."""
    harness = Harness(FlaskCharm)
    flask_container: Container = harness.model.unit.get_container(FLASK_CONTAINER_NAME)
    harness.set_can_connect(FLASK_CONTAINER_NAME, True)
    flask_container.make_dir("/srv/flask", make_parents=True)

    def python_cmd_handler(argv: list[str]) -> ExecResult:
        """Handle the python command execution inside the Flask container."""
        match argv:
            case [
                "python3",
                "-m",
                "gunicorn",
                "-c",
                "/srv/flask/gunicorn.conf.py",
                "app:app",
                "--check-config",
            ]:
                if flask_container.exists(
                    "/srv/flask/gunicorn.conf.py"
                ) and not flask_container.isdir("/srv/flask/gunicorn.conf.py"):
                    return ExecResult(0, "", "")
                return ExecResult(1, "", "")
            case _:
                raise RuntimeError(f"unknown command: {argv}")

    inject_register_command_handler(monkeypatch, harness)
    harness.register_command_handler(  # type: ignore # pylint: disable=no-member
        container=flask_container, executable="python3", handler=python_cmd_handler
    )

    yield harness
    harness.cleanup()
