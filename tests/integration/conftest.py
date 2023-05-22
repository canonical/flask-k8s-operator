# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for flask charm integration tests."""

import json

import pytest
import pytest_asyncio
from juju.application import Application
from juju.model import Model
from pytest import Config, FixtureRequest
from pytest_operator.plugin import OpsTest


@pytest_asyncio.fixture(scope="module", name="model")
async def fixture_model(ops_test: OpsTest) -> Model:
    """Return the current testing juju model."""
    assert ops_test.model
    return ops_test.model


@pytest.fixture(scope="module", name="external_hostname")
def external_hostname_fixture() -> str:
    """Return the external hostname for ingress-related tests."""
    return "juju.test"


@pytest.fixture(scope="module", name="traefik_app_name")
def traefik_app_name_fixture() -> str:
    """Return the name of the traefix application deployed for tests."""
    return "traefik-k8s"


@pytest_asyncio.fixture(scope="module", name="flask_app")
async def flask_app_fixture(
    ops_test: OpsTest,
    model: Model,
    pytestconfig: Config,
    external_hostname: str,
    traefik_app_name: str,
):
    """Build and deploy the flask charm."""
    app_name = "flask-k8s"
    charm = await ops_test.build_charm(".")
    resources = {"flask-app-image": pytestconfig.getoption("--flask-app-image")}
    flask_app = await model.deploy(
        charm, resources=resources, application_name=app_name, series="jammy"
    )
    await model.deploy(
        "traefik-k8s",
        application_name=traefik_app_name,
        trust=True,
        config={
            "external_hostname": external_hostname,
            "routing_mode": "subdomain",
        },
    )
    await model.wait_for_idle(apps=[app_name, traefik_app_name], raise_on_blocked=True)
    return flask_app


async def model_fixture(ops_test: OpsTest) -> Model:
    """Provide current test model."""
    assert ops_test.model
    model_config = {"logging-config": "<root>=INFO;unit=DEBUG"}
    await ops_test.model.set_config(model_config)
    return ops_test.model


@pytest_asyncio.fixture(scope="module", name="get_unit_ips")
async def fixture_get_unit_ips(ops_test: OpsTest):
    """Return an async function to retrieve unit ip addresses of a certain application."""

    async def get_unit_ips(application_name: str):
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

    return get_unit_ips


@pytest_asyncio.fixture
async def update_config(model: Model, request: FixtureRequest, flask_app: Application):
    """Update the flask application configuration.

    This fixture must be parameterized with changing charm configurations.
    """
    orig_config = {k: v.get("value") for k, v in (await flask_app.get_config()).items()}
    request_config = {k: str(v) for k, v in request.param.items()}
    await flask_app.set_config(request_config)
    await model.wait_for_idle(apps=[flask_app.name])

    yield request_config

    await flask_app.set_config(
        {k: v for k, v in orig_config.items() if k in request_config and v is not None}
    )
    await flask_app.reset_config([k for k in request_config if orig_config[k] is None])
    await model.wait_for_idle(apps=[flask_app.name])
