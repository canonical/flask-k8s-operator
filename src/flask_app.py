# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the FlaskApp class to represent the Flask application."""
import json

from charm_state import KNOWN_CHARM_CONFIG, CharmState
from constants import FLASK_ENV_CONFIG_PREFIX


class FlaskApp:  # pylint: disable=too-few-public-methods
    """A class representing the Flask application.

    Attrs:
        flask_environment: a Flask environment dictionary from the charm Flask configurations.
    """

    def __init__(self, charm_state: CharmState):
        """Initialize a new instance of the FlaskApp class.

        Args:
            charm_state: The state of the charm that the FlaskApp instance belongs to.
        """
        self._charm_state = charm_state

    @property
    def flask_environment(self) -> dict[str, str]:
        """Generate a Flask environment dictionary from the charm Flask configurations.

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
        flask_env = {
            k: v for k, v in self._charm_state.app_config.items() if k not in builtin_flask_config
        }
        flask_env.update(self._charm_state.flask_config)
        return {
            f"{FLASK_ENV_CONFIG_PREFIX}{k.upper()}": v if isinstance(v, str) else json.dumps(v)
            for k, v in flask_env.items()
        }
