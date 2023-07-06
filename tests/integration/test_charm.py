#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Flask charm."""
import asyncio
import json
import logging
import typing

import juju
import ops
import pytest
import requests
from juju.application import Application
from pytest_operator.plugin import OpsTest

# caused by pytest fixtures
# pylint: disable=too-many-arguments

logger = logging.getLogger(__name__)


async def test_flask_is_up(
    flask_app: Application,
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
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
    timeout: int,
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


async def test_default_secret_key(
    flask_app: Application,
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
):
    """
    arrange: build and deploy the flask charm.
    act: query flask secret key from the Flask server.
    assert: flask should have a default and secure secret configured.
    """
    secret_keys = [
        requests.get(f"http://{unit_ip}:8000/config/SECRET_KEY", timeout=10).json()
        for unit_ip in await get_unit_ips(flask_app.name)
    ]
    assert len(set(secret_keys)) == 1
    assert len(secret_keys[0]) > 10


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
        pytest.param({"flask_secret_key": "foobar"}, {"SECRET_KEY": "foobar"}, id="secret_key"),
    ],
    indirect=["update_config"],
)
@pytest.mark.usefixtures("update_config")
async def test_flask_config(
    flask_app: Application,
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
    excepted_config: dict,
):
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
async def test_invalid_flask_config(flask_app: Application, invalid_configs: tuple[str, ...]):
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


@pytest.mark.parametrize(
    "update_config, excepted_config",
    [
        pytest.param({"foo_str": "testing"}, {"FOO_STR": "testing"}, id="str"),
        pytest.param({"foo_int": 128}, {"FOO_INT": 128}, id="int"),
        pytest.param({"foo_bool": True}, {"FOO_BOOL": True}, id="bool"),
        pytest.param({"foo_dict": json.dumps({"a": 1})}, {"FOO_DICT": {"a": 1}}, id="dict"),
        pytest.param({"application_root": "/foo"}, {"APPLICATION_ROOT": "/"}, id="builtin"),
    ],
    indirect=["update_config"],
)
@pytest.mark.usefixtures("update_config")
async def test_app_config(
    flask_app: Application,
    excepted_config: dict[str, str | int | bool],
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
):
    """
    arrange: build and deploy the flask charm, and change Flask app configurations.
    act: none.
    assert: Flask application should receive the application configuration correctly.
    """
    for unit_ip in await get_unit_ips(flask_app.name):
        for config_key, config_value in excepted_config.items():
            assert (
                requests.get(f"http://{unit_ip}:8000/config/{config_key}", timeout=10).json()
                == config_value
            )


async def test_rotate_secret_key(
    model: juju.model.Model,
    flask_app: Application,
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
):
    """
    arrange: build and deploy the flask charm.
    act: run rotate-secret-key action on the leader unit.
    assert: Flask applications on every unit should have a new secret key configured.
    """
    unit_ips = await get_unit_ips(flask_app.name)
    secret_key = requests.get(f"http://{unit_ips[0]}:8000/config/SECRET_KEY", timeout=10).json()
    leader_unit = [u for u in flask_app.units if await u.is_leader_from_status()][0]
    action = await leader_unit.run_action("rotate-secret-key")
    await action.wait()
    assert action.results["status"] == "success"
    await model.wait_for_idle(status=ops.ActiveStatus.name)  # type: ignore
    for unit_ip in unit_ips:
        new_secret_key = requests.get(
            f"http://{unit_ip}:8000/config/SECRET_KEY", timeout=10
        ).json()
        assert len(new_secret_key) > 10
        assert new_secret_key != secret_key


async def test_with_ingress(
    ops_test: OpsTest,
    model: juju.model.Model,
    flask_app: Application,
    traefik_app,  # pylint: disable=unused-argument
    traefik_app_name: str,
    external_hostname: str,
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
):
    """
    arrange: build and deploy the flask charm, and deploy the ingress.
    act: relate the ingress charm with the Flask charm.
    assert: requesting the charm through traefik should return a correct response
    """
    await model.add_relation(flask_app.name, traefik_app_name)
    # mypy doesn't see that ActiveStatus has a name
    await model.wait_for_idle(status=ops.ActiveStatus.name)  # type: ignore

    traefik_ip = (await get_unit_ips(traefik_app_name))[0]
    response = requests.get(
        f"http://{traefik_ip}",
        headers={"Host": f"{ops_test.model_name}-{flask_app.name}.{external_hostname}"},
        timeout=5,
    )
    assert response.status_code == 200
    assert "Hello, World!" in response.text


async def test_nginx_route(
    model: juju.model.Model,
    flask_app: Application,
    nginx_ingress_integrator_app: Application,
):
    """
    arrange: build and deploy the flask charm, and deploy the nginx-ingress-integrator.
    act: relate the nginx-ingress-integrator charm with the Flask charm.
    assert: requesting the charm through nginx ingress should return a correct response
    """
    await model.add_relation(flask_app.name, nginx_ingress_integrator_app.name)
    # mypy doesn't see that ActiveStatus has a name
    await model.wait_for_idle(status=ops.ActiveStatus.name)  # type: ignore

    response = requests.get("http://127.0.0.1", headers={"Host": flask_app.name}, timeout=5)
    assert response.status_code == 200
    assert "Hello, World!" in response.text


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


async def test_prometheus_integration(
    model: juju.model.Model,
    prometheus_app_name: str,
    flask_app: Application,
    prometheus_app,  # pylint: disable=unused-argument
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
):
    """
    arrange: after Flask charm has been deployed.
    act: establish relations established with prometheus charm.
    assert: prometheus metrics endpoint for prometheus is active and prometheus has active scrape
        targets.
    """
    await model.add_relation(prometheus_app_name, flask_app.name)
    await model.wait_for_idle(apps=[flask_app.name, prometheus_app_name], status="active")

    for unit_ip in await get_unit_ips(prometheus_app_name):
        query_targets = requests.get(f"http://{unit_ip}:9090/api/v1/targets", timeout=10).json()
        assert len(query_targets["data"]["activeTargets"])


async def test_loki_integration(
    model: juju.model.Model,
    loki_app_name: str,
    flask_app: Application,
    loki_app,  # pylint: disable=unused-argument
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
):
    """
    arrange: after Flask charm has been deployed.
    act: establish relations established with loki charm.
    assert: loki joins relation successfully, logs are being output to container and to files for
        loki to scrape.
    """
    await model.add_relation(loki_app_name, flask_app.name)

    await model.wait_for_idle(
        apps=[flask_app.name, loki_app_name], status="active", idle_period=60
    )
    flask_ip = (await get_unit_ips(flask_app.name))[0]
    # populate the access log
    for _ in range(120):
        requests.get(f"http://{flask_ip}:8000", timeout=10)
        await asyncio.sleep(1)
    loki_ip = (await get_unit_ips(loki_app_name))[0]
    log_query = requests.get(
        f"http://{loki_ip}:3100/loki/api/v1/query",
        timeout=10,
        params={"query": f'{{juju_application="{flask_app.name}"}}'},
    ).json()
    assert len(log_query["data"]["result"])


async def test_grafana_integration(
    model: juju.model.Model,
    flask_app: Application,
    prometheus_app_name: str,
    loki_app_name: str,
    grafana_app_name: str,
    cos_apps,  # pylint: disable=unused-argument
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
):
    """
    arrange: after Flask charm has been deployed.
    act: establish relations established with grafana charm.
    assert: grafana Flask dashboard can be found.
    """
    await model.relate(
        f"{prometheus_app_name}:grafana-source", f"{grafana_app_name}:grafana-source"
    )
    await model.relate(f"{loki_app_name}:grafana-source", f"{grafana_app_name}:grafana-source")
    await model.relate(flask_app.name, grafana_app_name)

    await model.wait_for_idle(
        apps=[flask_app.name, prometheus_app_name, loki_app_name, grafana_app_name],
        status="active",
        idle_period=60,
    )

    action = await model.applications[grafana_app_name].units[0].run_action("get-admin-password")
    await action.wait()
    password = action.results["admin-password"]
    grafana_ip = (await get_unit_ips(grafana_app_name))[0]
    sess = requests.session()
    sess.post(
        f"http://{grafana_ip}:3000/login",
        json={
            "user": "admin",
            "password": password,
        },
    ).raise_for_status()
    datasources = sess.get(f"http://{grafana_ip}:3000/api/datasources", timeout=10).json()
    datasource_types = set(datasource["type"] for datasource in datasources)
    assert "loki" in datasource_types
    assert "prometheus" in datasource_types
    dashboards = sess.get(
        f"http://{grafana_ip}:3000/api/search",
        timeout=10,
        params={"query": "Flask Operator"},
    ).json()
    assert len(dashboards)
