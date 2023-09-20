<!-- markdownlint-disable -->

<a href="../src/databases.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `databases.py`
Provide the Databases class to handle database relations and state. 

**Global Variables**
---------------
- **FLASK_DATABASE_NAME**
- **FLASK_SUPPORTED_DB_INTERFACES**

---

<a href="../src/databases.py#L21"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `make_database_requirers`

```python
make_database_requirers(charm: CharmBase) → Dict[str, DatabaseRequires]
```

Create database requirer objects for the charm. 



**Args:**
 
 - <b>`charm`</b>:  The requiring charm. 

Returns: A dictionary which is the database uri environment variable name and the value is the corresponding database requirer object. 


---

<a href="../src/databases.py#L50"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_uris`

```python
get_uris(database_requirers: Dict[str, DatabaseRequires]) → Dict[str, str]
```

Compute DatabaseURI and return it. 



**Args:**
 
 - <b>`database_requirers`</b>:  Database requirers created by make_database_requirers. 



**Returns:**
 DatabaseURI containing details about the data provider integration 


---

## <kbd>class</kbd> `Databases`
A class handling databases relations and state. 

Attrs:  _charm: The main charm. Used for events callbacks  _databases: A dict of DatabaseRequires to store relations 

<a href="../src/databases.py#L98"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(
    charm: CharmBase,
    flask_app: FlaskApp,
    database_requirers: Dict[str, DatabaseRequires]
)
```

Initialize a new instance of the Databases class. 



**Args:**
 
 - <b>`charm`</b>:  The main charm. Used for events callbacks. 
 - <b>`flask_app`</b>:  The flask application manager object. 
 - <b>`database_requirers`</b>:  Database requirers created by make_database_requirers. 


---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 




