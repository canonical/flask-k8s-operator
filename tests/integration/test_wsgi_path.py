# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for flask-k8s charm webserver_wsgi_path configuration."""

import typing

import pytest
import requests
from juju.application import Application


@pytest.mark.parametrize(
    "update_config",
    [
        pytest.param({"webserver_wsgi_path": "app:app2"}, id="app2"),
    ],
    indirect=["update_config"],
)
@pytest.mark.usefixtures("update_config")
async def test_wsgi_config(
    flask_app: Application,
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
):
    """
    arrange: build and deploy the flask charm, and change flask related configurations.
    act: send HTTP request to the flask application.
    assert: the HTTP response should indicate that Flask application has changed to app2.
    """
    for unit_ip in await get_unit_ips(flask_app.name):
        response = requests.get(f"http://{unit_ip}:8000", timeout=10)
        assert response.ok
        assert response.text == "Hello, Many World!"
