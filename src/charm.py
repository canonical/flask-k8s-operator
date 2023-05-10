#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Flask Charm service."""

import logging
import typing

from charms.traefik_k8s.v1.ingress import IngressPerAppRequirer
from ops.charm import CharmBase, ConfigChangedEvent
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class FlaskCharm(CharmBase):
    """Flask Charm service."""

    _FLASK_APP_PORT = 8000

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self.config_service)
        self.ingress = IngressPerAppRequirer(
            self,
            port=self._FLASK_APP_PORT,
            # We're forced to use the app's service endpoint
            # as the ingress per app interface currently always routes to the leader.
            # https://github.com/canonical/traefik-k8s-operator/issues/159
            host=f"{self.app.name}-endpoints.{self.model.name}.svc.cluster.local",
            strip_prefix=True,
        )

    def config_service(self, event: ConfigChangedEvent) -> None:
        """Configure the flask pebble service layer.

        Args:
            event: the config-changed event that trigger this callback function.
        """
        container = self.unit.get_container("flask-app")
        if not container.can_connect():
            event.defer()
            return
        container.add_layer("flask-app", self.flask_layer(), combine=True)
        container.replan()
        self.unit.status = ActiveStatus()

    def flask_layer(self) -> dict:
        """Generate the pebble layer definition for flask application.

        Returns:
            The pebble layer definition for flask application.
        """
        return {
            "services": {
                "flask-app": {
                    "override": "replace",
                    "summary": "Flask application service",
                    "command": (
                        "/bin/python3 -m gunicorn --chdir /srv/flask/app app:app"
                        f" -b 0.0.0.0:{self._FLASK_APP_PORT}"
                    ),
                    "user": "flask",
                    "group": "flask",
                    "startup": "enabled",
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    main(FlaskCharm)
