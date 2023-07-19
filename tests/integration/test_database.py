#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Flask charm database integration."""
import logging

import juju
import ops
import pytest
import requests
from juju.application import Application

# caused by pytest fixtures
# pylint: disable=too-many-arguments

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "endpoint,db_name, db_channel, trust",
    [
        ("mysql/status", "mysql-k8s", "8.0/stable", True),
        ("postgresql/status", "postgresql-k8s", "14/stable", True),
    ],
)
async def test_with_database(
    flask_app: Application,
    model: juju.model.Model,
    get_unit_ips,
    endpoint: str,
    db_name: str,
    db_channel: str,
    trust: bool,
):
    """
    arrange: build and deploy the flask charm.
    act: deploy the database and relate it to the charm.
    assert: requesting the charm should return a correct response
    """
    db_app = await model.deploy(db_name, channel=db_channel, trust=trust)
    # mypy doesn't see that ActiveStatus has a name
    await model.wait_for_idle(status=ops.ActiveStatus.name)  # type: ignore

    await model.add_relation(flask_app.name, db_app.name)

    # mypy doesn't see that ActiveStatus has a name
    await model.wait_for_idle(status=ops.ActiveStatus.name)  # type: ignore

    for unit_ip in await get_unit_ips(flask_app.name):
        response = requests.get(f"http://{unit_ip}:8000/{endpoint}", timeout=5)
        assert response.status_code == 200
        assert "SUCCESS" == response.text
