# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the FlaskApp class to represent the Flask application."""
import json

from charm_state import CharmState
from consts import FLASK_ENV_CONFIG_PREFIX


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

        Returns:
            A dictionary representing the Flask environment variables.
        """
        flask_env = self._charm_state.app_config
        flask_env.update(self._charm_state.flask_config)
        return {
            f"{FLASK_ENV_CONFIG_PREFIX}{k.upper()}": json.dumps(v) for k, v in flask_env.items()
        }
