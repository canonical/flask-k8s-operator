# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm unit tests."""
import pytest
from ops.testing import Harness

from charm_state import CharmState
from exceptions import CharmConfigInvalidError

# pylint: disable=protected-access


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


@pytest.mark.parametrize(
    "charm_config, flask_config",
    [
        pytest.param({"flask_env": "prod"}, {"env": "prod"}, id="env"),
        pytest.param({"flask_debug": True}, {"debug": True}, id="debug"),
        pytest.param({"flask_secret_key": "1234"}, {"secret_key": "1234"}, id="secret_key"),
        pytest.param(
            {"flask_preferred_url_scheme": "http"},
            {"preferred_url_scheme": "HTTP"},
            id="preferred_url_scheme",
        ),
    ],
)
def test_charm_state_flask_config(
    harness: Harness, charm_config: dict, flask_config: dict
) -> None:
    """
    arrange: none
    act: set flask_* charm configurations.
    assert: flask_config in the charm state should reflect changes in charm configurations.
    """
    harness.begin()
    harness.update_config(charm_config)
    charm_state = CharmState.from_charm(harness.charm)
    assert charm_state.flask_config == flask_config


@pytest.mark.parametrize(
    "charm_config",
    [
        pytest.param({"flask_env": ""}, id="env"),
        pytest.param({"flask_secret_key": ""}, id="secret_key"),
        pytest.param(
            {"flask_preferred_url_scheme": "tls"},
            id="preferred_url_scheme",
        ),
    ],
)
def test_charm_state_invalid_flask_config(harness: Harness, charm_config: dict) -> None:
    """
    arrange: none
    act: set flask_* charm configurations to be invalid values.
    assert: the CharmState should raise a CharmConfigInvalidError exception
    """
    harness.begin()
    harness.update_config(charm_config)
    with pytest.raises(CharmConfigInvalidError) as exc:
        CharmState.from_charm(harness.charm)
    for config_key in charm_config:
        assert config_key in exc.value.msg
