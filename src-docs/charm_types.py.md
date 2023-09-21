<!-- markdownlint-disable -->

<a href="../src/charm_types.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `charm_types.py`
Type definitions for the Flask charm. 



---

## <kbd>class</kbd> `WebserverConfig`
Represent the configuration values for a web server. 



**Attributes:**
 
 - <b>`workers`</b>:  The number of workers to use for the web server, or None if not specified. 
 - <b>`threads`</b>:  The number of threads per worker to use for the web server,  or None if not specified. 
 - <b>`keepalive`</b>:  The time to wait for requests on a Keep-Alive connection,  or None if not specified. 
 - <b>`timeout`</b>:  The request silence timeout for the web server, or None if not specified. 





