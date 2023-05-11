# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "Hello, World!"
