<!-- markdownlint-disable -->

<a href="../src/secret_storage.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `secret_storage.py`
Provide the SecretStorage for managing the persistent secret storage for the Flask charm. 



---

## <kbd>class</kbd> `SecretStorage`
A class that manages secret keys required by the FlaskCharm. 

Attrs:  is_initialized: True if the SecretStorage has been initialized. 

<a href="../src/secret_storage.py#L23"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(charm: CharmBase)
```

Initialize the SecretStorage with a given FlaskCharm object. 



**Args:**
 
 - <b>`charm`</b> (FlaskCharm):  The FlaskCharm object that uses the SecretStorage. 


---

#### <kbd>property</kbd> is_initialized

Check if the SecretStorage has been initialized. 

It's an error to read or write the secret storage before initialization. 



**Returns:**
  True if SecretStorage is initialized, False otherwise. 

---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 



---

<a href="../src/secret_storage.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_flask_secret_key`

```python
get_flask_secret_key() → str
```

Retrieve the Flask secret key from the peer relation data. 



**Returns:**
  The Flask secret key. 

---

<a href="../src/secret_storage.py#L90"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `reset_flask_secret_key`

```python
reset_flask_secret_key() → None
```

Generate a new Flask secret key and store it within the peer relation data. 


