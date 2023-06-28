# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm unit tests for the flask_app module."""

# this is a unit test file
# pylint: disable=protected-access

import json

import pytest
from ops.testing import Harness

from charm_state import CharmState
from constants import FLASK_ENV_CONFIG_PREFIX
from flask_app import FlaskApp

FLASK_ENV_TEST_PARAMS = [
    pytest.param({"env": "test"}, id="env"),
    pytest.param({"permanent_session_lifetime": 1}, id="permanent_session_lifetime"),
    pytest.param({"debug": True}, id="debug"),
]


@pytest.mark.parametrize(
    "flask_config",
    FLASK_ENV_TEST_PARAMS,
)
def test_flask_env(harness: Harness, flask_config: dict):
    """
    arrange: create the Flask app object with a controlled charm state.
    act: none.
    assert: flask_environment generated by the Flask app object should be acceptable by Flask app.
    """
    harness.begin_with_initial_hooks()
    charm_state = CharmState(
        secret_storage=harness.charm._charm_state._secret_storage, flask_config=flask_config
    )
    flask_app = FlaskApp(charm_state=charm_state)
    env = flask_app.flask_environment()
    secret_key = env["FLASK_SECRET_KEY"]
    assert len(secret_key) > 10
    del env["FLASK_SECRET_KEY"]
    assert env == {
        f"{FLASK_ENV_CONFIG_PREFIX}{k.upper()}": v if isinstance(v, str) else json.dumps(v)
        for k, v in flask_config.items()
    }
