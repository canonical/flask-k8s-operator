# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""This module defines constants used throughout the Flask application."""

import pathlib

FLASK_CONTAINER_NAME = "flask-app"
FLASK_SERVICE_NAME = "flask"
FLASK_ENV_CONFIG_PREFIX = "FLASK_"
FLASK_DATABASE_NAME = "flask-app"
FLASK_SUPPORTED_DB_INTERFACES = {"mysql_client": "mysql", "postgresql_client": "postgresql"}
FLASK_BASE_DIR = pathlib.Path("/flask")
FLASK_APP_DIR = FLASK_BASE_DIR / "app"
FLASK_STATE_DIR = FLASK_BASE_DIR / "state"
