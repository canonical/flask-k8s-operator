#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Flask charm."""

import asyncio
import logging

import pytest
import pytest_asyncio
import requests
from ops.model import ActiveStatus, Application
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="module", name="flask_app")
async def flask_app_fixture(ops_test: OpsTest, pytestconfig: pytest.Config):
    """Build and deploy the flask charm."""
    assert ops_test.model
    app_name = "flask-k8s"
    charm = await ops_test.build_charm(".")
    resources = {"flask-app-image": pytestconfig.getoption("--flask-app-image")}
    deploy_result = await asyncio.gather(
        ops_test.model.deploy(
            charm, resources=resources, application_name=app_name, series="jammy"
        ),
        ops_test.model.wait_for_idle(apps=[app_name], raise_on_blocked=True),
    )
    return deploy_result[0]


async def test_flask_is_up(flask_app, get_unit_ips):
    """
    arrange: build and deploy the flask charm.
    act: send a request to the flask application managed by the flask charm.
    assert: the flask application should return a correct response.
    """
    for unit_ip in await get_unit_ips(flask_app.name):
        response = requests.get(f"http://{unit_ip}:8000", timeout=5)
        assert response.status_code == 200
        assert "Hello, World!" in response.text


async def test_with_ingress(
    ops_test: OpsTest,
    flask_app: Application,
    get_unit_ips,
):
    """
    arrange: build and deploy the flask charm.
    act: deploy the ingress, configure it and relate it to the charm.
    assert: requesting the charm through traefik should return a correct response
    """
    traefik_app = await ops_test.model.deploy("traefik-k8s", trust=True)
    await ops_test.model.wait_for_idle()

    external_hostname = "juju.local"
    await traefik_app.set_config(
        {
            "external_hostname": external_hostname,
            "routing_mode": "subdomain",
        }
    )
    await ops_test.model.wait_for_idle()

    await ops_test.model.add_relation(flask_app.name, traefik_app.name),

    # mypy doesn't see that ActiveStatus has a name
    await ops_test.model.wait_for_idle(status=ActiveStatus.name)  # type: ignore

    traefik_ip = next(await get_unit_ips(traefik_app.name))
    response = requests.get(
        f"http://{traefik_ip}",
        headers={"Host": f"{ops_test.model_name}-{flask_app.name}.{external_hostname}"},
        timeout=5,
    )
    assert response.status_code == 200
    assert "Hello, World!" in response.text
