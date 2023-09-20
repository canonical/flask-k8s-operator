<!-- markdownlint-disable -->

<a href="../src/webserver.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `webserver.py`
Provide the GunicornWebserver class to represent the gunicorn server. 

**Global Variables**
---------------
- **FLASK_SERVICE_NAME**


---

## <kbd>class</kbd> `GunicornWebserver`
A class representing a Gunicorn web server. 

Attrs:  command: the command to start the Gunicorn web server. 

<a href="../src/webserver.py#L29"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(charm_state: CharmState, flask_container: Container)
```

Initialize a new instance of the GunicornWebserver class. 



**Args:**
 
 - <b>`charm_state`</b>:  The state of the charm that the GunicornWebserver instance belongs to. 
 - <b>`flask_container`</b>:  The Flask container in this charm unit. 


---

#### <kbd>property</kbd> command

Get the command to start the Gunicorn web server. 



**Returns:**
  The command to start the Gunicorn web server. 



---

<a href="../src/webserver.py#L110"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `update_config`

```python
update_config(
    flask_environment: dict[str, str],
    is_webserver_running: bool
) → None
```

Update and apply the configuration file of the web server. 



**Args:**
 
 - <b>`flask_environment`</b>:  Environment variables used to run the flask application. 
 - <b>`is_webserver_running`</b>:  Indicates if the web server container is currently running. 



**Raises:**
 
 - <b>`CharmConfigInvalidError`</b>:  if the charm configuration is not valid. 


