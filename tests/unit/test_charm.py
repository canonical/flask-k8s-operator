# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm unit tests."""
import pytest
from ops.testing import Harness


@pytest.mark.usefixtures("mock_container_fs")
def test_flask_pebble_layer(harness: Harness) -> None:
    """
    arrange: none
    act: start the flask charm and set flask-app container to be ready.
    assert: flask charm should submit the correct flaks pebble layer to pebble.
    """
    harness.begin_with_initial_hooks()
    harness.set_can_connect(harness.model.unit.containers["flask-app"], True)
    harness.framework.reemit()
    flask_layer = harness.get_container_pebble_plan("flask-app").to_dict()["services"]["flask-app"]
    assert flask_layer == {
        "override": "replace",
        "summary": "Flask application service",
        "command": "python3 -m gunicorn -c /srv/flask/gunicorn.conf.py app:app",
        "startup": "enabled",
        "user": "flask",
        "group": "flask",
    }


def test_gunicorn_config(harness: Harness, mock_container_fs: dict[str, str]) -> None:
    """
    arrange: start the flask charm and set flask-app container to be ready.
    act: update gunicorn related charm configurations.
    assert: gunicorn configuration file inside the flask app container should change accordingly.
    """
    harness.begin_with_initial_hooks()
    harness.set_can_connect(harness.model.unit.containers["flask-app"], True)
    harness.framework.reemit()
    harness.update_config({"webserver_workers": 1})
    assert mock_container_fs.get("/srv/flask/gunicorn.conf.py") == "\n".join(
        ["bind = ['0.0.0.0:8000']", "chdir = '/srv/flask/app'", "workers = 1"]
    )
    harness.update_config(
        {"webserver_threads": 2, "webserver_timeout": 3, "webserver_keepalive": 4},
        unset=["webserver_workers"],
    )
    assert mock_container_fs.get("/srv/flask/gunicorn.conf.py") == "\n".join(
        [
            "bind = ['0.0.0.0:8000']",
            "chdir = '/srv/flask/app'",
            "threads = 2",
            "keepalive = 4",
            "timeout = 3",
        ]
    )
