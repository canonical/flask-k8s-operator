# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for flask charm integration tests."""

import json

import pytest_asyncio
from pytest_operator.plugin import OpsTest


@pytest_asyncio.fixture(scope="module", name="get_unit_ips")
async def fixture_get_unit_ips(ops_test: OpsTest):
    """Return an async function to retrieve unit ip addresses of a certain application."""

    async def _get_unit_ips(application_name: str):
        """Retrieve unit ip addresses of a certain application.

        Returns:
            a list containing unit ip addresses.
        """
        _, status, _ = await ops_test.juju("status", "--format", "json")
        status = json.loads(status)
        units = status["applications"][application_name]["units"]
        return (
            unit_status["address"]
            for _, unit_status in sorted(units.items(), key=lambda kv: int(kv[0].split("/")[-1]))
        )

    yield _get_unit_ips
