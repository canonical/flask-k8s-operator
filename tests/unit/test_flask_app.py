# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm unit tests for the flask_app module."""

# this is a unit test file
# pylint: disable=protected-access

import json
import typing
import unittest.mock

import pytest
from xiilib.flask.charm_state import CharmState
from xiilib.flask.constants import FLASK_ENV_CONFIG_PREFIX
from xiilib.flask.flask_app import FlaskApp


@pytest.mark.parametrize(
    "flask_config",
    [
        pytest.param({"env": "test"}, id="env"),
        pytest.param({"permanent_session_lifetime": 1}, id="permanent_session_lifetime"),
        pytest.param({"debug": True}, id="debug"),
    ],
)
def test_flask_env(flask_config: dict, database_migration_mock):
    """
    arrange: create the Flask app object with a controlled charm state.
    act: none.
    assert: flask_environment generated by the Flask app object should be acceptable by Flask app.
    """
    charm_state = CharmState(
        flask_secret_key="foobar",
        is_secret_storage_ready=True,
        flask_config=flask_config,
    )
    flask_app = FlaskApp(
        charm=unittest.mock.MagicMock(),
        charm_state=charm_state,
        webserver=unittest.mock.MagicMock(),
        database_migration=database_migration_mock,
    )
    env = flask_app._flask_environment()
    assert env["FLASK_SECRET_KEY"] == "foobar"
    del env["FLASK_SECRET_KEY"]
    assert env == {
        f"{FLASK_ENV_CONFIG_PREFIX}{k.upper()}": v if isinstance(v, str) else json.dumps(v)
        for k, v in flask_config.items()
    }


HTTP_PROXY_TEST_PARAMS = [
    pytest.param({}, {}, id="no_env"),
    pytest.param({"JUJU_CHARM_NO_PROXY": "127.0.0.1"}, {"no_proxy": "127.0.0.1"}, id="no_proxy"),
    pytest.param(
        {"JUJU_CHARM_HTTP_PROXY": "http://proxy.test"},
        {"http_proxy": "http://proxy.test"},
        id="http_proxy",
    ),
    pytest.param(
        {"JUJU_CHARM_HTTPS_PROXY": "http://proxy.test"},
        {"https_proxy": "http://proxy.test"},
        id="https_proxy",
    ),
    pytest.param(
        {
            "JUJU_CHARM_HTTP_PROXY": "http://proxy.test",
            "JUJU_CHARM_HTTPS_PROXY": "http://proxy.test",
        },
        {"http_proxy": "http://proxy.test", "https_proxy": "http://proxy.test"},
        id="http_https_proxy",
    ),
]


@pytest.mark.parametrize(
    "set_env, expected",
    HTTP_PROXY_TEST_PARAMS,
)
def test_http_proxy(
    set_env: typing.Dict[str, str],
    expected: typing.Dict[str, str],
    monkeypatch,
    database_migration_mock,
):
    """
    arrange: set juju charm http proxy related environment variables.
    act: generate a flask environment.
    assert: flask_environment generated should contain proper proxy environment variables.
    """
    for set_env_name, set_env_value in set_env.items():
        monkeypatch.setenv(set_env_name, set_env_value)
    charm_state = CharmState(
        flask_secret_key="",
        is_secret_storage_ready=True,
        flask_config={},
    )
    flask_app = FlaskApp(
        charm=unittest.mock.MagicMock(),
        charm_state=charm_state,
        webserver=unittest.mock.MagicMock(),
        database_migration=database_migration_mock,
    )
    env = flask_app._flask_environment()
    expected_env: typing.Dict[str, typing.Optional[str]] = {
        "http_proxy": None,
        "https_proxy": None,
        "no_proxy": None,
    }
    expected_env.update(expected)
    for env_name, env_value in expected_env.items():
        assert env.get(env_name) == env.get(env_name.upper()) == env_value
