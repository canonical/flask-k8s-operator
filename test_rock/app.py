# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
import time

from flask import Flask, request, jsonify

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


@app.route("/config/<config_name>")
def config(config_name: str):
    return jsonify(app.config.get(config_name))
