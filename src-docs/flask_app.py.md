<!-- markdownlint-disable -->

<a href="../src/flask_app.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `flask_app.py`
Provide the FlaskApp class to represent the Flask application. 

**Global Variables**
---------------
- **KNOWN_CHARM_CONFIG**
- **FLASK_ENV_CONFIG_PREFIX**
- **FLASK_SERVICE_NAME**


---

## <kbd>class</kbd> `FlaskApp`
Flask application manager. 

<a href="../src/flask_app.py#L21"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(
    charm: CharmBase,
    charm_state: CharmState,
    webserver: GunicornWebserver
)
```

Construct the FlaskApp instance. 



**Args:**
 
 - <b>`charm`</b>:  The main charm object. 
 - <b>`charm_state`</b>:  The state of the charm. 
 - <b>`webserver`</b>:  The webserver manager object. 




---

<a href="../src/flask_app.py#L90"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `restart_flask`

```python
restart_flask() → None
```

Restart or start the flask service if not started with the latest configuration. 

Raise CharmConfigInvalidError if the configuration is not valid. 


