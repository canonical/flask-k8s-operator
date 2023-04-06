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

APP_NAME = "flask-k8s"


@pytest_asyncio.fixture
async def build_and_deploy(ops_test: OpsTest, pytestconfig: pytest.Config):
    """Build and deploy the flask charm."""
    assert ops_test.model
    charm = await ops_test.build_charm(".")
    resources = {"flask-app-image": pytestconfig.getoption("--flask-app-image")}
    await asyncio.gather(
        ops_test.model.deploy(
            charm, resources=resources, application_name=APP_NAME, series="jammy"
        ),
        ops_test.model.wait_for_idle(apps=[APP_NAME], raise_on_blocked=True),
    )


@pytest.mark.usefixtures("build_and_deploy")
async def test_flask_is_up(get_unit_ips):
    """
    arrange: build and deploy the flask charm.
    act: send a request to the flask application managed by the flask charm.
    assert: the flask application should return a correct response.
    """
    for unit_ip in await get_unit_ips(APP_NAME):
        response = requests.get(f"http://{unit_ip}:8080", timeout=5)
        assert response.status_code == 200
        assert "Hello, World!" in response.text
