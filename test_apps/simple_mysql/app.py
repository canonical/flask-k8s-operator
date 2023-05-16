# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from urllib.parse import urlparse
from flask import Flask, g
import pymysql
import pymysql.cursors

app = Flask(__name__)
app.config.from_prefixed_env()

def get_database():
    if 'database' not in g:
        if app.config.get("DATABASE_URI"):
            uri_parts = urlparse(app.config["DATABASE_URI"])
            g.database = pymysql.connect(
                host=uri_parts.hostname,
                user=uri_parts.username,
                password=uri_parts.password,
                database=uri_parts.path[1:],
                port=uri_parts.port,
                cursorclass=pymysql.cursors.DictCursor,
            )
        return None
    return g.database


@app.teardown_appcontext
def teardown_database(exception):
    database = g.pop('database', None)
    if database is not None:
        database.close()


@app.route("/")
def simple_mysql():
    if (database := get_database()):
        with database.cursor() as cursor:
            sql = "SELECT version()"
            cursor.execute(sql)
            cursor.fetchone()
            return "SUCCESS"
    return "FAIL"


@app.route("/env")
def simple_mysql_env():
    return app.config.get("DATABASE_URI")
