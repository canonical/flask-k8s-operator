#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Flask charm."""

import logging
import typing

import pytest
import requests
from juju.application import Application

logger = logging.getLogger(__name__)


async def test_flask_is_up(
    flask_app: Application, get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]]
):
    """
    arrange: build and deploy the flask charm.
    act: send a request to the flask application managed by the flask charm.
    assert: the flask application should return a correct response.
    """
    for unit_ip in await get_unit_ips(flask_app.name):
        response = requests.get(f"http://{unit_ip}:8000", timeout=5)
        assert response.status_code == 200
        assert "Hello, World!" in response.text


@pytest.mark.parametrize("update_config", [{"webserver_timeout": 7}], indirect=True)
@pytest.mark.usefixtures("update_config")
async def test_flask_webserver_config(
    flask_app: Application, get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]]
):
    """
    arrange: build and deploy the flask charm, and change the gunicorn timeout configuration.
    act: send long-running requests to the flask application managed by the flask charm.
    assert: the gunicorn should restart the worker if the request duration exceeds the timeout.
    """
    for unit_ip in await get_unit_ips(flask_app.name):
        assert requests.get(f"http://{unit_ip}:8000/sleep?duration=6", timeout=10).ok
        with pytest.raises(requests.ConnectionError):
            requests.get(f"http://{unit_ip}:8000/sleep?duration=8", timeout=10)


@pytest.mark.parametrize(
    "update_config, expected_config",
    [
        ({"flask_debug": True}, {"DEBUG": True}),
        (
            {"flask_permanent_session_lifetime": 10, "flask_secret_key": "123"},
            {"PERMANENT_SESSION_LIFETIME": 10.0, "SECRET_KEY": "123"},
        ),
        (
            {"flask_application_root": "/test"},
            {"APPLICATION_ROOT": "/test"},
        ),
    ],
    indirect=["update_config"],
)
@pytest.mark.usefixtures("update_config")
async def test_flask_config(
    flask_app: Application,
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
    expected_config: dict,
):
    """
    arrange: build and deploy the flask charm, and change the gunicorn timeout configuration.
    act: update the flask configuration via flask related charm configurations.
    assert: flask application should receive the correct configurations via environment variables.
    """
    expected_config = {
        "APPLICATION_ROOT": "/",
        "DEBUG": False,
        "ENV": "production",
        "PERMANENT_SESSION_LIFETIME": 2678400.0,
        "PREFERRED_URL_SCHEME": "http",
        "SECRET_KEY": None,
        "SESSION_COOKIE_SECURE": False,
        **expected_config,
    }
    for unit_ip in await get_unit_ips(flask_app.name):
        flask_config = requests.get(f"http://{unit_ip}:8000/conf", timeout=10).json()
        assert expected_config == flask_config
