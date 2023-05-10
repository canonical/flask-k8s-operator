# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the FlaskApp class to represent the Flask application."""

from charm_state import CharmState


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
        return {f"FLASK_{k.upper()}": str(v) for k, v in self._charm_state.flask_config.items()}
