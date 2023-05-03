# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""pytest fixtures for the integration test."""

# pylint: disable=protected-access

import typing

import pytest
from ops.model import Container
from ops.pebble import ExecError
from ops.testing import Harness

from charm import FlaskCharm
from charm_types import ExecResult
from consts import FLASK_CONTAINER_NAME


def inject_register_command_handler(monkeypatch: pytest.MonkeyPatch, harness: Harness):
    handler_table = {}

    class ExecProcessStub:
        def __init__(self, command: list[str], exit_code: int, stdout: str, stderr: str):
            self._command = command
            self._exit_code = exit_code
            self._stdout = stdout
            self._stderr = stderr

        def wait_output(self):
            if self._exit_code == 0:
                return self._stdout, self._stderr
            else:
                raise ExecError(
                    command=self._command,
                    exit_code=self._exit_code,
                    stdout=self._stdout,
                    stderr=self._stderr,
                )

    def exec_stub(command: list[str], **_kwargs):
        executable = command[0]
        handler = handler_table[executable]
        exit_code, stdout, stderr = handler(command)
        return ExecProcessStub(command=command, exit_code=exit_code, stdout=stdout, stderr=stderr)

    def register_command_handler(
        container: Container | str,
        executable: str,
        handler=typing.Callable[[list[str]], typing.Tuple[int, str, str]],
    ):
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
    # As a user, I would like to access the container prior to the harness started to preload
    # the container with some files (/etc, /srv, etc). For now, the container is accessible
    # with the following API, but it requires you to set can connect before using it. Setting can
    # connect here can interfere with the actual test case.
    flask_container: Container = harness.model.unit.get_container(FLASK_CONTAINER_NAME)
    harness.set_can_connect(FLASK_CONTAINER_NAME, True)
    flask_container.make_dir("/srv/flask", make_parents=True)

    def python_cmd_handler(argv: list[str]) -> ExecResult:
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
                else:
                    return ExecResult(1, "", "")
            case _:
                raise RuntimeError(f"unknown command: {argv}")

    inject_register_command_handler(monkeypatch, harness)
    # imaginary API for the testing harness to register a callback function for command
    # execution, the callback function should accept an ``argv`` argument and return a 3-tuple of
    # exit code, stdout, stderr to simulate the command execution.
    harness.register_command_handler(
        container=flask_container, executable="python3", handler=python_cmd_handler
    )

    yield harness
    harness.cleanup()
