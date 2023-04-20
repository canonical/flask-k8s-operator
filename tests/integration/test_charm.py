#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Flask charm."""

import logging
import threading
import time
import typing

import pytest
import requests
from juju.application import Application

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
        ({"webserver_timeout": 30, "webserver_threads": 2, "webserver_workers": 3}, 6),
        ({"webserver_timeout": 30, "webserver_threads": 1, "webserver_workers": 5}, 5),
        ({"webserver_timeout": 30, "webserver_threads": 3, "webserver_workers": 3}, 9),
    ],
    indirect=["update_config"],
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
        threads = [threading.Thread(target=blocking_request) for _ in range(max_concurrency - 1)]
        for thread in threads:
            thread.start()
        time_start = time.time()
        assert requests.get(f"http://{unit_ip}:8000/sleep?duration=0", timeout=10).ok
        assert time.time() - time_start < 1
        blocking_thread = threading.Thread(target=blocking_request)
        blocking_thread.start()
        time_start = time.time()
        assert requests.get(f"http://{unit_ip}:8000/sleep?duration=0", timeout=10).ok
        assert time.time() - time_start > 3
