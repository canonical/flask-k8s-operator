#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Flask charm."""

import logging

import juju
import requests
from ops.model import ActiveStatus, Application
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


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
    model: juju.model.Model,
    flask_app: Application,
    get_unit_ips,
):
    """
    arrange: build and deploy the flask charm.
    act: deploy the ingress, configure it and relate it to the charm.
    assert: requesting the charm through traefik should return a correct response
    """
    traefik_app = await model.deploy("traefik-k8s", trust=True)
    await model.wait_for_idle()

    external_hostname = "juju.local"
    await traefik_app.set_config(
        {
            "external_hostname": external_hostname,
            "routing_mode": "subdomain",
        }
    )
    await model.wait_for_idle()

    await model.add_relation(flask_app.name, traefik_app.name)

    # mypy doesn't see that ActiveStatus has a name
    await model.wait_for_idle(status=ActiveStatus.name)  # type: ignore

    traefik_ip = next(await get_unit_ips(traefik_app.name))
    response = requests.get(
        f"http://{traefik_ip}",
        headers={"Host": f"{ops_test.model_name}-{flask_app.name}.{external_hostname}"},
        timeout=5,
    )
    assert response.status_code == 200
    assert "Hello, World!" in response.text


async def test_with_mysql(
    model: juju.model.Model,
    flask_app: Application,
    get_unit_ips,
):
    """
    arrange: build and deploy the flask charm.
    act: deploy the ingress, configure it and relate it to the charm.
    assert: requesting the charm through traefik should return a correct response
    """
    mysql_app = await model.deploy("mysql-k8s", channel="8.0/stable")
    await model.wait_for_idle()

    await model.add_relation(flask_app.name, mysql_app.name)

    # mypy doesn't see that ActiveStatus has a name
    await model.wait_for_idle(status=ActiveStatus.name)  # type: ignore

    for unit_ip in await get_unit_ips(flask_app.name):
        response = requests.get(f"http://{unit_ip}:8000", timeout=5)
        assert response.status_code == 200
        assert "SUCCESS" in response.text
