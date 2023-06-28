# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm unit tests for the webserver module."""

# this is a unit test file
# pylint: disable=protected-access

import textwrap
import unittest.mock

import ops
import pytest
from ops.testing import Harness

from charm_state import CharmState
from constants import FLASK_CONTAINER_NAME
from flask_app import FlaskApp
from webserver import GunicornWebserver

FLASK_BASE_DIR = "/srv/flask"

GUNICORN_CONFIG_TEST_PARAMS = [
    pytest.param(
        {"webserver_workers": 10},
        textwrap.dedent(
            f"""\
                bind = ['0.0.0.0:8000']
                chdir = '{FLASK_BASE_DIR}/app'
                accesslog = '/var/log/flask/access.log'
                errorlog = '/var/log/flask/error.log'
                statsd_host = 'localhost:9125'
                workers = 10"""
        ),
        id="workers=10",
    ),
    pytest.param(
        {"webserver_threads": 2, "webserver_timeout": 3, "webserver_keepalive": 4},
        textwrap.dedent(
            f"""\
                bind = ['0.0.0.0:8000']
                chdir = '{FLASK_BASE_DIR}/app'
                accesslog = '/var/log/flask/access.log'
                errorlog = '/var/log/flask/error.log'
                statsd_host = 'localhost:9125'
                threads = 2
                keepalive = 4
                timeout = 3"""
        ),
        id="threads=2,timeout=3,keepalive=4",
    ),
]


@pytest.mark.parametrize("charm_state_params, config_file", GUNICORN_CONFIG_TEST_PARAMS)
def test_gunicorn_config(
    harness: Harness,
    charm_state_params,
    config_file,
) -> None:
    """
    arrange: create the Gunicorn webserver object with a controlled charm state generated by the
        charm_state_params parameter.
    act: invoke the update_config method of the webserver object.
    assert: gunicorn configuration file inside the flask app container should change accordingly.
    """
    harness.begin_with_initial_hooks()
    container: ops.Container = harness.model.unit.get_container(FLASK_CONTAINER_NAME)
    harness.set_can_connect(FLASK_CONTAINER_NAME, True)
    charm_state = CharmState(
        secret_storage=harness.charm._charm_state._secret_storage, **charm_state_params
    )
    flask_app = FlaskApp(
        charm_state=charm_state,
    )
    webserver = GunicornWebserver(
        charm_state=charm_state, flask_container=container, flask_app=flask_app
    )
    webserver.update_config(is_webserver_running=False)
    assert container.pull(f"{FLASK_BASE_DIR}/gunicorn.conf.py").read() == config_file


@pytest.mark.parametrize("is_running", [True, False])
def test_webserver_reload(monkeypatch, harness: Harness, is_running):
    """
    arrange: put an empty file in the Flask container and create a webserver object with default
        charm state.
    act: run the update_config method of the webserver object with different server running status.
    assert: webserver object should send signal to the Gunicorn server based on the running status.
    """
    harness.begin_with_initial_hooks()
    container: ops.Container = harness.model.unit.get_container(FLASK_CONTAINER_NAME)
    harness.set_can_connect(FLASK_CONTAINER_NAME, True)
    container.push(f"{FLASK_BASE_DIR}/gunicorn.conf.py", "")
    charm_state = CharmState(
        secret_storage=harness.charm._charm_state._secret_storage, flask_config={}
    )
    flask_app = FlaskApp(charm_state=charm_state)
    webserver = GunicornWebserver(
        charm_state=charm_state, flask_container=container, flask_app=flask_app
    )
    send_signal_mock = unittest.mock.MagicMock()
    monkeypatch.setattr(container, "send_signal", send_signal_mock)
    webserver.update_config(is_webserver_running=is_running)
    assert send_signal_mock.call_count == (1 if is_running else 0)
