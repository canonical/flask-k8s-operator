#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Flask charm."""

# pylint: disable=too-many-arguments

import logging
import typing

import juju
import pytest
import requests
from juju.application import Application
from ops.model import ActiveStatus
from pytest_operator.plugin import OpsTest

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


@pytest.mark.parametrize(
    "update_config, timeout",
    [
        pytest.param({"webserver_timeout": 7}, 7, id="timeout=7"),
        pytest.param({"webserver_timeout": 5}, 5, id="timeout=5"),
        pytest.param({"webserver_timeout": 3}, 3, id="timeout=3"),
    ],
    indirect=["update_config"],
)
@pytest.mark.usefixtures("update_config")
async def test_flask_webserver_timeout(
    flask_app: Application,
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
    timeout,
):
    """
    arrange: build and deploy the flask charm, and change the gunicorn timeout configuration.
    act: send long-running requests to the flask application managed by the flask charm.
    assert: the gunicorn should restart the worker if the request duration exceeds the timeout.
    """
    safety_timeout = timeout + 3
    for unit_ip in await get_unit_ips(flask_app.name):
        assert requests.get(
            f"http://{unit_ip}:8000/sleep?duration={timeout - 1}", timeout=safety_timeout
        ).ok
        with pytest.raises(requests.ConnectionError):
            requests.get(
                f"http://{unit_ip}:8000/sleep?duration={timeout + 1}", timeout=safety_timeout
            )


@pytest.mark.parametrize(
    "update_config, excepted_config",
    [
        pytest.param({"flask_env": "testing"}, {"ENV": "testing"}, id="env"),
        pytest.param(
            {"flask_permanent_session_lifetime": 100},
            {"PERMANENT_SESSION_LIFETIME": 100},
            id="permanent_session_lifetime",
        ),
        pytest.param({"flask_debug": True}, {"DEBUG": True}, id="debug"),
    ],
    indirect=["update_config"],
)
@pytest.mark.usefixtures("update_config")
async def test_flask_config(flask_app, get_unit_ips, excepted_config):
    """
    arrange: build and deploy the flask charm, and change flask related configurations.
    act: query flask configurations from the Flask server.
    assert: the flask configuration should match flask related charm configurations.
    """
    for unit_ip in await get_unit_ips(flask_app.name):
        for config_key, config_value in excepted_config.items():
            assert (
                requests.get(f"http://{unit_ip}:8000/config/{config_key}", timeout=10).json()
                == config_value
            )


@pytest.mark.parametrize(
    "update_config, invalid_configs",
    [
        pytest.param(
            {"flask_permanent_session_lifetime": -1},
            ("permanent_session_lifetime",),
            id="permanent_session_lifetime",
        ),
        pytest.param(
            {"flask_preferred_url_scheme": "TLS"},
            ("preferred_url_scheme",),
            id="preferred_url_scheme",
        ),
    ],
    indirect=["update_config"],
)
@pytest.mark.usefixtures("update_config")
async def test_invalid_flask_config(flask_app: Application, invalid_configs):
    """
    arrange: build and deploy the flask charm, and change flask related configurations
        to certain invalid values.
    act: none.
    assert: flask charm should enter the blocked status and the status message should show
        invalid configuration options.
    """
    assert flask_app.status == "blocked"
    for invalid_config in invalid_configs:
        assert invalid_config in flask_app.status_message
    for unit in flask_app.units:
        assert unit.workload_status == "blocked"
        for invalid_config in invalid_configs:
            assert invalid_config in unit.workload_status_message


async def test_with_ingress(
    ops_test: OpsTest,
    model: juju.model.Model,
    flask_app: Application,
    traefik_app_name: str,
    external_hostname: str,
    get_unit_ips,
):
    """
    arrange: build and deploy the flask charm, and deploy the ingress.
    act: relate the ingress charm with the Flask charm.
    assert: requesting the charm through traefik should return a correct response
    """
    await model.add_relation(flask_app.name, traefik_app_name)
    # mypy doesn't see that ActiveStatus has a name
    await model.wait_for_idle(status=ActiveStatus.name)  # type: ignore

    traefik_ip = next(await get_unit_ips(traefik_app_name))
    response = requests.get(
        f"http://{traefik_ip}",
        headers={"Host": f"{ops_test.model_name}-{flask_app.name}.{external_hostname}"},
        timeout=5,
    )
    assert response.status_code == 200
    assert "Hello, World!" in response.text
