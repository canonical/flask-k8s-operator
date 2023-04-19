# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
import time

from flask import Flask, request

app = Flask(__name__)
app.config.from_prefixed_env()


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/sleep")
def sleep():
    duration_seconds = int(request.args.get("duration"))
    time.sleep(duration_seconds)
    return ""


@app.route("/conf")
def conf():
    return {
        "DEBUG": app.debug,
        "ENV": app.env,
        "SECRET_KEY": app.secret_key,
        "PERMANENT_SESSION_LIFETIME": app.permanent_session_lifetime.total_seconds(),
        "APPLICATION_ROOT": app.config.get("APPLICATION_ROOT"),
        "SESSION_COOKIE_SECURE": app.config.get("SESSION_COOKIE_SECURE"),
        "PREFERRED_URL_SCHEME": app.config.get("PREFERRED_URL_SCHEME"),
    }
