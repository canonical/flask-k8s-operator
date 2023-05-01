# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm unit tests."""

# pylint: disable=protected-access

import unittest.mock

from ops.testing import Harness

from charm import FlaskCharm

FLASK_BASE_DIR = "/srv/flask"


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
        "command": f"python3 -m gunicorn -c {FLASK_BASE_DIR}/gunicorn.conf.py app:app",
        "startup": "enabled",
        "user": "flask",
        "group": "flask",
    }


def test_webserver_reload(
    monkeypatch,
    harness: Harness,
):
    """
    arrange: start the flask charm and start the flask service by invoking the config-changed
        callback.
    act: invoke the callback function of the config-changed event with a different charm state.
    assert: charm should send a reload signal to the webserver to reload the configuration.
    """
    mock_reload_webserver = unittest.mock.MagicMock()
    monkeypatch.setattr(FlaskCharm, "reload_webserver", mock_reload_webserver)
    harness.begin_with_initial_hooks()
    harness.set_can_connect(harness.model.unit.containers["flask-app"], True)
    harness.charm._on_config_changed(unittest.mock.MagicMock())

    assert not mock_reload_webserver.called

    harness.update_config({"webserver": 100})

    assert mock_reload_webserver.call_count == 1
