# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""pytest fixtures for the integration test."""

# pylint: disable=protected-access

import typing

import pytest
from ops.testing import Harness, _TestingFilesystem

from charm import FlaskCharm
from charm_types import ExecResult


@pytest.fixture(name="harness")
def harness_fixture(monkeypatch) -> typing.Generator[Harness, None, None]:
    """Ops testing framework harness fixture."""
    harness = Harness(FlaskCharm)
    flask_container_fs = harness.fs[FlaskCharm._FLASK_CONTAINER_NAME]
    flask_container_fs.add_dir("/srv/flask")
    flask_container_exec = harness.exec[FlaskCharm._FLASK_CONTAINER_NAME]

    def python_exec_handler(argv: list[str]) -> ExecResult:
        match argv:
            case [
                "python"
                "-m",
                "gunicorn",
                "-c",
                "/srv/flask/gunicorn.conf.py",
                "app:app",
                "--check-config",
            ]:
                if flask_container_fs.is_file("/srv/flask/gunicorn.conf.py"):
                    return ExecResult(0, "", "")
                else:
                    return ExecResult(1, "", "")
            case _:
                raise RuntimeError(f"unknown command: {argv}")

    flask_container_exec.register_executable(executable="python", handler=python_exec_handler)

    yield harness
    harness.cleanup()
