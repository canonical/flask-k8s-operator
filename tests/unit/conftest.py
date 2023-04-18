# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""pytest fixtures for the integration test."""

# pylint: disable=protected-access

import typing

import ops.testing
import pytest

from charm import FlaskCharm
from charm_types import ExecResult


@pytest.fixture(name="harness")
def harness_fixture(monkeypatch) -> typing.Generator[ops.testing.Harness, None, None]:
    """Ops testing framework harness fixture."""
    harness = ops.testing.Harness(FlaskCharm)
    orig_send_signal = ops.testing._TestingPebbleClient.send_signal

    def patched_send_signal(self, sig, service_names):
        """Patch a bug in the ops testing framework temporarily."""
        return orig_send_signal(self, sig, *service_names)

    monkeypatch.setattr(ops.testing._TestingPebbleClient, "send_signal", patched_send_signal)
    yield harness
    harness.cleanup()


@pytest.fixture
def mock_container_fs(monkeypatch) -> dict[str, str]:
    """Patch the pull_file and push_file method of the charm."""
    mock_fs: dict[str, str] = {}
    monkeypatch.setattr(FlaskCharm, "push_file", mock_fs.__setitem__)
    monkeypatch.setattr(FlaskCharm, "pull_file", mock_fs.get)
    return mock_fs


@pytest.fixture
def mock_container_exec(monkeypatch):
    """Patch the exec method of the charm."""
    monkeypatch.setattr(FlaskCharm, "exec", lambda *_: ExecResult(0, "", ""))
