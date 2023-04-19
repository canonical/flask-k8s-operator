# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the FlaskApp class to represent the Flask application."""

import json

from charm_state import CharmState


class FlaskApp:  # pylint: disable=too-few-public-methods
    """A class representing the Flask application."""

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
        environ = {}
        if self._charm_state.flask_config.env:
            environ["FLASK_ENV"] = self._charm_state.flask_config.env
        if self._charm_state.flask_config.debug:
            environ["FLASK_DEBUG"] = "true"
        if self._charm_state.flask_config.secret_key:
            secret_key = self._charm_state.flask_config.secret_key
            try:
                is_number = isinstance(json.loads(secret_key), (int, float))
            except json.JSONDecodeError:
                is_number = False
            environ["FLASK_SECRET_KEY"] = json.dumps(secret_key) if is_number else secret_key
        if self._charm_state.flask_config.permanent_session_lifetime is not None:
            environ["FLASK_PERMANENT_SESSION_LIFETIME"] = str(
                int(self._charm_state.flask_config.permanent_session_lifetime.total_seconds())
            )
        if self._charm_state.flask_config.application_root is not None:
            environ["FLASK_APPLICATION_ROOT"] = self._charm_state.flask_config.application_root
        if self._charm_state.flask_config.session_cookie_secure:
            environ["FLASK_SESSION_COOKIE_SECURE"] = "true"
        if self._charm_state.flask_config.preferred_url_scheme is not None:
            environ[
                "FLASK_PREFERRED_URL_SCHEME"
            ] = self._charm_state.flask_config.preferred_url_scheme
        return environ
