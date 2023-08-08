# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the FlaskApp class to represent the Flask application."""
import json
import logging
import shlex

import ops

from charm_state import KNOWN_CHARM_CONFIG, CharmState
from constants import FLASK_ENV_CONFIG_PREFIX, FLASK_SERVICE_NAME
from webserver import GunicornWebserver

logger = logging.getLogger(__name__)


def _flask_environment(charm_state: CharmState) -> dict[str, str]:
    """Generate a Flask environment dictionary from the charm Flask configurations.

    Args:
        charm_state: The state of the charm.

    The Flask environment generation follows these rules:
        1. User-defined configuration cannot overwrite built-in Flask configurations, even if
            the built-in Flask configuration value is None (undefined).
        2. Boolean and integer-typed configuration values will be JSON encoded before
            being passed to Flask.
        3. String-typed configuration values will be passed to Flask as environment variables
            directly.

    Returns:
        A dictionary representing the Flask environment variables.
    """
    builtin_flask_config = [
        c.removeprefix("flask_") for c in KNOWN_CHARM_CONFIG if c.startswith("flask_")
    ]
    flask_env = {k: v for k, v in charm_state.app_config.items() if k not in builtin_flask_config}
    flask_env.update(charm_state.flask_config)
    env = {
        f"{FLASK_ENV_CONFIG_PREFIX}{k.upper()}": v if isinstance(v, str) else json.dumps(v)
        for k, v in flask_env.items()
    }
    secret_key_env = f"{FLASK_ENV_CONFIG_PREFIX}SECRET_KEY"
    if secret_key_env not in env:
        env[secret_key_env] = charm_state.flask_secret_key
    for proxy_variable in ("http_proxy", "https_proxy", "no_proxy"):
        proxy_value = getattr(charm_state.proxy, proxy_variable)
        if proxy_value:
            env[proxy_variable] = str(proxy_value)
            env[proxy_variable.upper()] = str(proxy_value)
    env.update(charm_state.database_uris)
    return env


def _flask_layer(charm_state: CharmState, webserver: GunicornWebserver) -> ops.pebble.LayerDict:
    """Generate the pebble layer definition for flask application.

    Args:
        charm_state: The state of the charm
        webserver: The webserver manager object

    Returns:
        The pebble layer definition for flask application.
    """
    environment = _flask_environment(charm_state=charm_state)
    return ops.pebble.LayerDict(
        services={
            FLASK_SERVICE_NAME: {
                "override": "replace",
                "summary": "Flask application service",
                "command": shlex.join(webserver.command),
                "startup": "enabled",
                "environment": environment,
            }
        },
    )


def restart_flask(
    charm: ops.CharmBase, charm_state: CharmState, webserver: GunicornWebserver
) -> None:
    """Restart or start the flask service if not started with the latest configuration.

    Raise CharmConfigInvalidError if the configuration is not valid.

    Args:
        charm: The main charm object.
        charm_state: The state of the charm.
        webserver: The webserver manager object.
    """
    container = charm.unit.get_container("flask-app")
    if not container.can_connect():
        logger.info("pebble client in the Flask container is not ready")
        return
    if not charm_state.is_secret_storage_ready:
        logger.info("secret storage is not initialized")
        return
    container.add_layer("flask-app", _flask_layer(charm_state, webserver), combine=True)
    is_webserver_running = container.get_service(FLASK_SERVICE_NAME).is_running()
    webserver.update_config(
        flask_environment=_flask_environment(charm_state),
        is_webserver_running=is_webserver_running,
    )
    container.replan()
