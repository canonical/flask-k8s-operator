# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
import time
from urllib.parse import urlparse

import psycopg
import pymysql
import pymysql.cursors
from flask import Flask, g, request

app = Flask(__name__)
app.config.from_prefixed_env()


def get_mysql_database():
    """Get the mysql db connection."""
    if "mysql_db" not in g:
        if app.config.get("MYSQL_DB_CONNECT_URI"):
            uri_parts = urlparse(app.config["MYSQL_DB_CONNECT_URI"])
            g.database = pymysql.connect(
                host=uri_parts.hostname,
                user=uri_parts.username,
                password=uri_parts.password,
                database=uri_parts.path[1:],
                port=uri_parts.port,
                cursorclass=pymysql.cursors.DictCursor,
            )
        return None
    return g.mysql_db


def get_postgresql_database():
    """Get the postgresql db connection."""
    if "postgresql_db" not in g:
        if app.config.get("POSTGRESQL_DB_CONNECT_URI"):
            uri_parts = urlparse(app.config["POSTGRESQL_DB_CONNECT_URI"])
            g.database = psycopg.connect(
                host=uri_parts.hostname,
                user=uri_parts.username,
                password=uri_parts.password,
                database=uri_parts.path[1:],
                port=uri_parts.port,
            )
        return None
    return g.postgresql_db


@app.teardown_appcontext
def teardown_database(exception):
    """Tear down databases connections."""
    mysql_db = g.pop("mysql_db", None)
    if mysql_db is not None:
        mysql_db.close()
    postgresql_db = g.pop("postgresql_db", None)
    if postgresql_db is not None:
        postgresql_db.close()


@app.route("/")
def hello_world():
    """Simple hello world endpoint."""
    return "Hello, World!"


@app.route("/sleep")
def sleep():
    """Sleep endpoint."""
    duration_seconds = int(request.args.get("duration"))
    time.sleep(duration_seconds)
    return ""


@app.route("/mysql/status")
def mysql_status():
    """Mysql status endpoint."""
    if database := get_mysql_database():
        with database.cursor() as cursor:
            sql = "SELECT version()"
            cursor.execute(sql)
            cursor.fetchone()
            return "SUCCESS"
    return "FAIL"


@app.route("/mysql/env")
def mysql_env():
    """Mysql env endpoint."""
    return app.config.get("MYSQL_DB_CONNECT_URI")


@app.route("/postgresql/status")
def postgresql_status():
    """Postgresql status endpoint."""
    if database := get_postgresql_database():
        with database.cursor() as cursor:
            sql = "SELECT version()"
            cursor.execute(sql)
            cursor.fetchone()
            return "SUCCESS"
    return "FAIL"


@app.route("/postgresql/env")
def postgresql_env():
    """Postgresql env endpoint."""
    return app.config.get("MYSQL_DB_CONNECT_URI")
