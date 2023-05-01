# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""pytest fixtures for the integration test."""

# pylint: disable=protected-access

import typing

import pytest
from ops.model import Container
from ops.testing import Harness

from charm import FlaskCharm
from charm_types import ExecResult


@pytest.fixture(name="harness")
def harness_fixture(monkeypatch) -> typing.Generator[Harness, None, None]:
    """Ops testing framework harness fixture."""
    harness = Harness(FlaskCharm)

    # the imaginary API for the testing harness to expose the container before harness began
    # so, we can preload the container virtual filesystem and inspect and assert the content of
    # the filesystem in test cases
    flask_container: Container = harness.containers[FlaskCharm._FLASK_CONTAINER_NAME]
    flask_container.make_dir("/srv/flask")

    def python_exec_handler(argv: list[str]) -> ExecResult:
        match argv:
            case [
                "python" "-m",
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

    # another imaginary API for the testing harness to register a callback function for command
    # execution, the callback function should accept an ``argv`` argument and return a 3-tuple of
    # exit code, stdout, stderr to simulate the command execution.
    flask_container.register_executable(executable="python", handler=python_exec_handler)

    yield harness
    harness.cleanup()
