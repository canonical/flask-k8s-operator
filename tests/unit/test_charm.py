# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm unit tests."""
import pytest
from ops.testing import Harness

FLASK_BASE_DIR = "/srv/flask"


@pytest.mark.parametrize(
    "flask_config, flask_env",
    [
        ({"flask_debug": True}, {"FLASK_DEBUG": "true"}),
        ({"flask_env": "testing"}, {"FLASK_ENV": "testing"}),
        ({"flask_secret_key": "abc"}, {"FLASK_SECRET_KEY": "abc"}),
        ({"flask_secret_key": "123"}, {"FLASK_SECRET_KEY": '"123"'}),
        ({"flask_permanent_session_lifetime": 123}, {"FLASK_PERMANENT_SESSION_LIFETIME": "123"}),
        ({"flask_application_root": "/test"}, {"FLASK_APPLICATION_ROOT": "/test"}),
        ({"flask_session_cookie_secure": True}, {"FLASK_SESSION_COOKIE_SECURE": "true"}),
        ({"flask_preferred_url_scheme": "HTTPS"}, {"FLASK_PREFERRED_URL_SCHEME": "HTTPS"}),
    ],
)
@pytest.mark.usefixtures("mock_container_fs", "mock_container_exec")
def test_flask_pebble_layer(
    harness: Harness, flask_config: dict[str, str], flask_env: dict
) -> None:
    """
    arrange: none
    act: start the flask charm and set flask-app container to be ready.
    assert: flask charm should submit the correct flaks pebble layer to pebble.
    """
    harness.begin_with_initial_hooks()
    harness.set_can_connect(harness.model.unit.containers["flask-app"], True)
    harness.framework.reemit()
    harness.update_config(flask_config)
    flask_layer = harness.get_container_pebble_plan("flask-app").to_dict()["services"]["flask-app"]
    assert flask_layer == {
        "override": "replace",
        "summary": "Flask application service",
        "command": f"python3 -m gunicorn -c {FLASK_BASE_DIR}/gunicorn.conf.py app:app",
        "startup": "enabled",
        "user": "flask",
        "group": "flask",
        "environment": flask_env,
    }


@pytest.mark.usefixtures("mock_container_exec")
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
    assert mock_container_fs.get(f"{FLASK_BASE_DIR}/gunicorn.conf.py") == "\n".join(
        ["bind = ['0.0.0.0:8000']", f"chdir = '{FLASK_BASE_DIR}/app'", "workers = 1"]
    )
    harness.update_config(
        {"webserver_threads": 2, "webserver_timeout": 3, "webserver_keepalive": 4},
        unset=["webserver_workers"],
    )
    assert mock_container_fs.get(f"{FLASK_BASE_DIR}/gunicorn.conf.py") == "\n".join(
        [
            "bind = ['0.0.0.0:8000']",
            f"chdir = '{FLASK_BASE_DIR}/app'",
            "threads = 2",
            "keepalive = 4",
            "timeout = 3",
        ]
    )
