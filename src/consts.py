# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""This module defines constants used throughout the Flask application."""

FLASK_CONTAINER_NAME = "flask-app"
FLASK_SERVICE_NAME = "flask-app"
FLASK_ENV_CONFIG_PREFIX = "FLASK_"
KNOWN_CHARM_CONFIG = (
    "webserver_workers",
    "webserver_threads",
    "webserver_keepalive",
    "webserver_timeout",
    "flask_env",
    "flask_debug",
    "flask_secret_key",
    "flask_permanent_session_lifetime",
    "flask_application_root",
    "flask_session_cookie_secure",
    "flask_preferred_url_scheme",
)
