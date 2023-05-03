#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Flask charm."""

import asyncio
import logging
import threading
import time
import typing

import juju
import pytest
import requests
from ops.model import ActiveStatus, Application
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


async def test_flask_is_up(
    flask_app: Application, get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]]
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
    [({"webserver_timeout": 7}, 7), ({"webserver_timeout": 5}, 5), ({"webserver_timeout": 3}, 3)],
    indirect=["update_config"],
    ids=["timeout-7", "timeout-5", "timeout-3"],
)
@pytest.mark.usefixtures("update_config")
async def test_flask_webserver_timeout(
    flask_app: Application,
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
    timeout,
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


@pytest.mark.parametrize(
    "update_config, max_concurrency",
    [
        ({"webserver_timeout": 15, "webserver_threads": 2, "webserver_workers": 3}, 6),
        ({"webserver_timeout": 15, "webserver_threads": 1, "webserver_workers": 5}, 5),
        ({"webserver_timeout": 15, "webserver_threads": 3, "webserver_workers": 3}, 9),
    ],
    indirect=["update_config"],
    ids=["concurrency-6", "concurrency-5", "concurrency-9"],
)
@pytest.mark.usefixtures("update_config")
async def test_flask_webserver_threads_workers(
    flask_app: Application,
    get_unit_ips: typing.Callable[[str], typing.Awaitable[tuple[str, ...]]],
    max_concurrency: int,
):
    """
    arrange: build and deploy the flask charm, and change the gunicorn timeout configuration.
    act: send long-running requests to the flask application managed by the flask charm.
    assert: the gunicorn should restart the worker if the request duration exceeds the timeout.
    """

    def blocking_request():
        """Send a 5 seconds blocking request to the Flask server."""
        assert requests.get(f"http://{unit_ip}:8000/sleep?duration=5", timeout=10).ok

    for unit_ip in await get_unit_ips(flask_app.name):
        # wait for webserver to reload
        await asyncio.sleep(30)
        threads = [threading.Thread(target=blocking_request) for _ in range(max_concurrency - 1)]
        for thread in threads:
            thread.start()
        # wait for connections established in threads
        await asyncio.sleep(1)
        time_start = time.time()
        assert requests.get(f"http://{unit_ip}:8000/sleep?duration=0", timeout=10).ok
        assert time.time() - time_start < 1
        blocking_thread = threading.Thread(target=blocking_request)
        blocking_thread.start()
        # wait for the blocking connection established
        await asyncio.sleep(1)
        time_start = time.time()
        assert requests.get(f"http://{unit_ip}:8000/sleep?duration=0", timeout=10).ok
        assert time.time() - time_start > 3
        for thread in threads:
            thread.join()
        blocking_thread.join()


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
