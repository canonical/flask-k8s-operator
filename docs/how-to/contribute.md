# How to Contribute

## Overview

This document explains the processes and practices recommended for contributing
enhancements to the Flask operator.

- Before developing enhancements to this charm,
  consider [opening an issue](https://github.com/canonical/flask-k8s-operator/issues)
  to explain your use case.
- If you want to discuss your use-cases or proposed implementation, you can
  reach us
  at [Canonical Mattermost public channel](https://chat.charmhub.io/charmhub/channels/charm-dev)
  or [Discourse](https://discourse.charmhub.io/).
- Familiarizing yourself with
  the [Charmed Operator Framework](https://juju.is/docs/sdk) will be beneficial
  when working on new features or bug fixes.
- All enhancements require a review before merging. Code reviews typically
  examine code quality, test coverage, and user experience for Juju operators of
  this charm.
- Please help us ensure easy-to-review branches by rebasing your pull request
  branch onto the `main` branch. This also avoids merge commits and creates a
  linear Git commit history.
- For additional information on contributing, refer to
  our [Contributing Guide](https://github.com/canonical/is-charms-contributing-guide).

## Developing

### Building from Source

To build and deploy the flask-k8s charm from source, follow the steps below.

#### Docker Image Build

Build your Flask application image, and to allow microk8s to pick up the locally
built image, you must export the image and import it within microk8s.

#### Build the Charm

Build the charm locally using charmcraft. It should output a .charm file.

```bash
charmcraft pack
```

### Deploy Flask

Deploy the locally built Flask charm with the following command.

```bash
juju deploy ./flask-k8s_ubuntu-22.04-amd64_ubuntu-20.04-amd64.charm \
  --resource flask-app-image=localhost:32000/flask:test \
  --resource statsd-prometheus-exporter-image=prom/statsd-exporter
```

Monitor your local flask-k8s charm's progress through the stages of the
deployment with `juju status --watch 2s`.

### Testing

Use the following commands to run the tests:

- `tox`: Runs all of the basic checks (`lint`, `unit`, `static`,
  and `coverage-report`).
- `tox -e fmt`: Formats the code using `black` and `isort`.
- `tox -e lint`: Runs a range of static code analyses to check the code.
- `tox -e static`: Runs other checks such as `bandit` for security issues.
- `tox -e unit`: Runs the unit tests.
- `tox -e integration`: Runs the integration tests. Integration tests
  require [additional arguments](https://github.com/canonical/flask-k8s-operator/blob/main/tests/conftest.py)
  depending on the test module.

## Canonical Contributor Agreement

Canonical welcomes contributions to the Flask Operator. If you're interested in
contributing to the solution, please check out
our [contributor agreement](https://ubuntu.com/legal/contributors).
