# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for flask-k8s charm sentinel check."""

from juju.model import Model
from pytest import Config
from pytest_operator.plugin import OpsTest


async def test_sentinel_check(
    pytestconfig: Config,
    ops_test: OpsTest,
    model: Model,
):
    """
    arrange: none.
    act: build and deploy the flask-k8s charm with sentinel image as the flask-app-image.
    assert: flask-k8s charm should enter blocked state.
    """
    charm = await ops_test.build_charm(".")
    resources = {
        "flask-app-image": pytestconfig.getoption("--sentinel-image"),
        "statsd-prometheus-exporter-image": "prom/statsd-exporter",
    }
    app_name = "flask-sentinel"
    flask_app = await model.deploy(
        charm, resources=resources, application_name=app_name, series="jammy"
    )
    await model.wait_for_idle(apps=[app_name])
    assert flask_app.status == "blocked"
    assert flask_app.status_message == (
        "charm requires a Flask app image, "
        "redeploy with '--resource flask-app-image=<your-image>'"
    )
