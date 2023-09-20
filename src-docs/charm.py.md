<!-- markdownlint-disable -->

<a href="../src/charm.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `charm.py`
Flask Charm service. 

**Global Variables**
---------------
- **FLASK_CONTAINER_NAME**


---

## <kbd>class</kbd> `FlaskCharm`
Flask Charm service. 

<a href="../src/charm.py#L29"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(*args: Any) → None
```

Initialize the instance. 



**Args:**
 
 - <b>`args`</b>:  passthrough to CharmBase. 


---

#### <kbd>property</kbd> app

Application that this unit is part of. 

---

#### <kbd>property</kbd> charm_dir

Root directory of the charm as it is running. 

---

#### <kbd>property</kbd> config

A mapping containing the charm's config and current values. 

---

#### <kbd>property</kbd> meta

Metadata of this charm. 

---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 

---

#### <kbd>property</kbd> unit

Unit that this execution is responsible for. 



---

<a href="../src/charm.py#L80"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `container`

```python
container() → Container
```

Get the flask application workload container controller. 

Return:  The controller of the flask application workload container. 



**Raises:**
 
 - <b>`PebbleNotReadyError`</b>:  if the pebble service inside the container is not ready while the  ``require_connected`` is set to True. 


