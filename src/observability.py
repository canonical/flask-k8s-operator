# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the Observability class to represent the observability stack for Flask application."""

from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from ops import CharmBase

from charm_state import CharmState


class Observability:  # pylint: disable=too-few-public-methods
    """A class representing the observability stack for Flask application."""

    def __init__(self, charm: CharmBase, charm_state: CharmState):
        """Initialize a new instance of the Observability class.

        Args:
            charm: The charm object that the Observability instance belongs to.
            charm_state: The state of the charm that the Observability instance belongs to.
        """
        self._metrics_endpoint = MetricsEndpointProvider(
            charm,
            relation_name="metrics-endpoint",
            jobs=[{"static_configs": [{"targets": ["*:80"]}]}],
        )
        self._logging = LogProxyConsumer(
            charm,
            relation_name="logging",
            log_files=[str(charm_state.flask_access_log), str(charm_state.flask_error_log)],
            container_name="flask-app",
        )
        self._grafana_dashboards = GrafanaDashboardProvider(
            charm, relation_name="grafana-dashboard"
        )
