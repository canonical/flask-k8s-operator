# Flask-k8s Charm Tutorial

## What You'll Do

In this tutorial, we'll work on:

- Constructing a Flask container
- Deploying the [flask-k8s charm](https://charmhub.io/flask-k8s)

The flask-k8s charm simplifies the deployment of scalable Flask applications,
in addition to facilitating charm operation by interfacing with the Canonical
Observability Stack (COS). We'll guide you step-by-step through the entire
deployment process to set up a basic Flask deployment.

## Prerequisites

For deploying the flask-k8s charm, ensure you have a juju installation
bootstrapped with any kubernetes controller. To bootstrap your juju
installation with microk8s, refer to the microk8s [installation
documentation](https://juju.is/docs/olm/microk8s).

## Setting up a Tutorial Model

To manage resources effectively and to separate this tutorial's workload from
your usual work, we recommend creating a new model using the following command.

```
juju add-model flask-tutorial
```

## Building the Flask Container

Unlike some other Kubernetes charms, the flask-k8s charm operates in a 'bring
your own container' mode, meaning it doesn't provide a workload container. A
container image for use with the flask-k8s charm must meet the following
requirements:

- It should have gunicorn installed as a global Python package
- The Flask application should be situated in the `/flask/app` directory
- The Flask WSGI application should be located at `/flask/app/app.py`, with
  the variable name `app`
- The Flask application must invoke `app.config.from_prefixed_env()` to receive
  configuration

The flask-k8s repository offers a sample [rockcraft
project](https://github.com/canonical/flask-k8s-operator/tree/main/sample_rock)
to guide you in building a compliant OCI image for the flask-k8s charm.

After creating the Flask application image, upload it to a container registry.
For guidance on using microk8s' built-in registry, refer to this [online
guide](https://microk8s.io/docs/registry-built-in).

## Deploying the flask-k8s charm

To deploy the flask-k8s charm from the edge channel, use the command below:

```
juju deploy flask-k8s --channel edge --resource flask-app-image=localhost:32000/flask-app:test 
```

To monitor your deployment progress across various stages, use this command:

```
juju status --color --watch 2s
```

At this point, you can access your Flask application at `http://<UNIT_IP>:8000`.

## Cleaning up the Environment

Well done! You've successfully completed the flask-k8s tutorial. To remove the
model environment you created during this tutorial, use the following command.

```
juju destroy model flask-tutorial -y
```
