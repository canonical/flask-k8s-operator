<!-- markdownlint-disable -->

<a href="../src/charm_state.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `charm_state.py`
This module defines the CharmState class which represents the state of the Flask charm. 

**Global Variables**
---------------
- **KNOWN_CHARM_CONFIG**


---

## <kbd>class</kbd> `CharmState`
Represents the state of the Flask charm. 

Attrs:  webserver_config: the web server configuration file content for the charm.  flask_config: the value of the flask_config charm configuration.  app_config: user-defined configurations for the Flask application.  base_dir: the base directory of the Flask application.  database_uris: a mapping of available database environment variable to database uris.  flask_dir: the path to the Flask directory.  flask_wsgi_app_path: the path to the Flask directory.  flask_port: the port number to use for the Flask server.  flask_access_log: the file path for the Flask access log.  flask_error_log: the file path for the Flask error log.  flask_statsd_host: the statsd server host for Flask metrics.  flask_secret_key: the charm managed flask secret key.  is_secret_storage_ready: whether the secret storage system is ready.  proxy: proxy information. 

<a href="../src/charm_state.py#L120"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(
    app_config: dict[str, int | str | bool] | None = None,
    database_uris: dict[str, str] | None = None,
    flask_config: dict[str, int | str] | None = None,
    flask_secret_key: str | None = None,
    is_secret_storage_ready: bool,
    webserver_workers: int | None = None,
    webserver_threads: int | None = None,
    webserver_keepalive: int | None = None,
    webserver_timeout: int | None = None,
    webserver_wsgi_path: str | None = None
)
```

Initialize a new instance of the CharmState class. 



**Args:**
 
 - <b>`app_config`</b>:  User-defined configuration values for the Flask configuration. 
 - <b>`flask_config`</b>:  The value of the flask_config charm configuration. 
 - <b>`flask_secret_key`</b>:  The secret storage manager associated with the charm. 
 - <b>`database_uris`</b>:  The database uri environment variables. 
 - <b>`is_secret_storage_ready`</b>:  whether the secret storage system is ready. 
 - <b>`webserver_workers`</b>:  The number of workers to use for the web server,  or None if not specified. 
 - <b>`webserver_threads`</b>:  The number of threads per worker to use for the web server,  or None if not specified. 
 - <b>`webserver_keepalive`</b>:  The time to wait for requests on a Keep-Alive connection,  or None if not specified. 
 - <b>`webserver_timeout`</b>:  The request silence timeout for the web server,  or None if not specified. 
 - <b>`webserver_wsgi_path`</b>:  The WSGI application path, or None if not specified. 


---

#### <kbd>property</kbd> app_config

Get the value of user-defined Flask application configurations. 



**Returns:**
  The value of user-defined Flask application configurations. 

---

#### <kbd>property</kbd> base_dir

Get the base directory of the Flask application. 



**Returns:**
  The base directory of the Flask application. 

---

#### <kbd>property</kbd> flask_access_log

Returns the file path for the Flask access log. 



**Returns:**
  The file path for the Flask access log. 

---

#### <kbd>property</kbd> flask_config

Get the value of the flask_config charm configuration. 



**Returns:**
  The value of the flask_config charm configuration. 

---

#### <kbd>property</kbd> flask_dir

Gets the path to the Flask directory. 



**Returns:**
  The path to the Flask directory. 

---

#### <kbd>property</kbd> flask_error_log

Returns the file path for the Flask error log. 



**Returns:**
  The file path for the Flask error log. 

---

#### <kbd>property</kbd> flask_port

Gets the port number to use for the Flask server. 



**Returns:**
  The port number to use for the Flask server. 

---

#### <kbd>property</kbd> flask_secret_key

Return the flask secret key stored in the SecretStorage. 

It's an error to read the secret key before SecretStorage is initialized. 



**Returns:**
  The flask secret key stored in the SecretStorage. 



**Raises:**
 
 - <b>`RuntimeError`</b>:  raised when accessing flask secret key before secret storage is ready 

---

#### <kbd>property</kbd> flask_statsd_host

Returns the statsd server host for Flask metrics. 



**Returns:**
  The statsd server host for Flask metrics. 

---

#### <kbd>property</kbd> flask_wsgi_app_path

Gets the Flask WSGI application in pattern $(MODULE_NAME):$(VARIABLE_NAME). 

The MODULE_NAME should be relative to the flask directory. 



**Returns:**
  The path to the Flask WSGI application. 

---

#### <kbd>property</kbd> is_secret_storage_ready

Return whether the secret storage system is ready. 



**Returns:**
  Whether the secret storage system is ready. 

---

#### <kbd>property</kbd> proxy

Get charm proxy information from juju charm environment. 



**Returns:**
  charm proxy information in the form of `ProxyConfig`. 

---

#### <kbd>property</kbd> webserver_config

Get the web server configuration file content for the charm. 



**Returns:**
  The web server configuration file content for the charm. 



---

<a href="../src/charm_state.py#L181"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `from_charm`

```python
from_charm(
    charm: 'FlaskCharm',
    secret_storage: SecretStorage,
    database_uris: dict[str, str]
) → CharmState
```

Initialize a new instance of the CharmState class from the associated charm. 



**Args:**
 
 - <b>`charm`</b>:  The charm instance associated with this state. 
 - <b>`secret_storage`</b>:  The secret storage manager associated with the charm. 
 - <b>`database_uris`</b>:  The database uri environment variables. 

Return: The CharmState instance created by the provided charm. 



**Raises:**
 
 - <b>`CharmConfigInvalidError`</b>:  if the charm configuration is invalid. 


---

## <kbd>class</kbd> `FlaskConfig`
Represent Flask builtin configuration values. 

Attrs:  env: what environment the Flask app is running in, by default it's 'production'.  debug: whether Flask debug mode is enabled.  secret_key: a secret key that will be used for securely signing the session cookie  and can be used for any other security related needs by your Flask application.  permanent_session_lifetime: set the cookie’s expiration to this number of seconds in the  Flask application permanent sessions.  application_root: inform the Flask application what path it is mounted under by the  application / web server.  session_cookie_secure: set the secure attribute in the Flask application cookies.  preferred_url_scheme: use this scheme for generating external URLs when not in a request  context in the Flask application. 




---

<a href="../src/charm_state.py#L71"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `to_upper`

```python
to_upper(value: str) → str
```

Convert the string field to uppercase. 



**Args:**
 
 - <b>`value`</b>:  the input value. 



**Returns:**
 The string converted to uppercase. 


---

## <kbd>class</kbd> `ProxyConfig`
Configuration for accessing Jenkins through proxy. 



**Attributes:**
 
 - <b>`http_proxy`</b>:  The http proxy URL. 
 - <b>`https_proxy`</b>:  The https proxy URL. 
 - <b>`no_proxy`</b>:  Comma separated list of hostnames to bypass proxy. 





