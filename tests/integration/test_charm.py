#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Flask charm."""

import asyncio
import logging

import pytest
import pytest_asyncio
import requests
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
