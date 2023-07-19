#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Flask charm proxy setting."""

import requests
from juju.model import Model
from pytest import Config


async def test_proxy(build_charm: str, model: Model, pytestconfig: Config, get_unit_ips):
    """Build and deploy the flask charm."""
    app_name = "flask-k8s"
    await model.set_config(
        {
            "juju-http-proxy": "http://proxy.test",
            "juju-https-proxy": "http://proxy.test",
            "juju-no-proxy": "127.0.0.1,10.0.0.1",
        }
    )
    resources = {
        "flask-app-image": pytestconfig.getoption("--test-flask-image"),
        "statsd-prometheus-exporter-image": "prom/statsd-exporter",
    }
    await model.deploy(build_charm, resources=resources, application_name=app_name, series="jammy")
    await model.wait_for_idle(raise_on_blocked=True)
    unit_ips = await get_unit_ips(app_name)
    for unit_ip in unit_ips:
        response = requests.get(f"http://{unit_ip}/env", timeout=5)
        assert response.status_code == 200
        env = response.json()
        assert env["http_proxy"] == "http://proxy.test"
        assert env["HTTP_PROXY"] == "http://proxy.test"
        assert env["https_proxy"] == "http://proxy.test"
        assert env["HTTPS_PROXY"] == "http://proxy.test"
        assert env["no_proxy"] == "127.0.0.1,10.0.0.1"
        assert env["NO_proxy"] == "127.0.0.1,10.0.0.1"
