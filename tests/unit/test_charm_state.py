# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask charm state unit tests."""

# this is a unit test file
# pylint: disable=protected-access

import pytest
from ops.testing import Harness

from charm_state import CharmState
from exceptions import CharmConfigInvalidError

CHARM_STATE_FLASK_CONFIG_TEST_PARAMS = [
    pytest.param(
        {"flask_env": "prod"}, {"env": "prod", "preferred_url_scheme": "HTTPS"}, id="env"
    ),
    pytest.param(
        {"flask_debug": True}, {"debug": True, "preferred_url_scheme": "HTTPS"}, id="debug"
    ),
    pytest.param(
        {"flask_secret_key": "1234"},
        {"secret_key": "1234", "preferred_url_scheme": "HTTPS"},
        id="secret_key",
    ),
    pytest.param(
        {"flask_preferred_url_scheme": "http"},
        {"preferred_url_scheme": "HTTP"},
        id="preferred_url_scheme",
    ),
]


@pytest.mark.parametrize("charm_config, flask_config", CHARM_STATE_FLASK_CONFIG_TEST_PARAMS)
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
    charm_state = CharmState.from_charm(
        secret_storage=harness.charm._charm_state._secret_storage,
        charm=harness.charm,
        databases=harness.charm._databases,
    )
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
        CharmState.from_charm(
            secret_storage=harness.charm._charm_state._secret_storage,
            charm=harness.charm,
            databases=harness.charm._databases,
        )
    for config_key in charm_config:
        assert config_key in exc.value.msg


@pytest.mark.parametrize(
    "charm_config, wsgi_path",
    [
        pytest.param({}, "app:app", id="default"),
        pytest.param({"webserver_wsgi_path": "foo.bar:app2"}, "foo.bar:app2", id="non-default"),
    ],
)
def test_charm_state_wsgi_path(harness: Harness, charm_config: dict, wsgi_path: str) -> None:
    """
    arrange: none.
    act: set the wsgi_path charm configuration to different values
    assert: the CharmState should reflect those changes
    """
    harness.begin()
    harness.update_config(charm_config)
    charm_state = CharmState.from_charm(
        secret_storage=harness.charm._charm_state._secret_storage,
        charm=harness.charm,
        databases=harness.charm._databases,
    )
    assert charm_state.flask_wsgi_app_path == wsgi_path
