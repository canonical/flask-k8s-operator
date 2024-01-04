# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the Observability class to represent the observability stack for Flask application."""

import textwrap

import ops
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider

from charm_state import CharmState
from constants import FLASK_CONTAINER_NAME


class Observability(ops.Object):  # pylint: disable=too-few-public-methods
    """A class representing the observability stack for Flask application."""

    def __init__(self, charm: ops.CharmBase, charm_state: CharmState):
        """Initialize a new instance of the Observability class.

        Args:
            charm: The charm object that the Observability instance belongs to.
            charm_state: The state of the charm that the Observability instance belongs to.
        """
        super().__init__(charm, "observability")
        self._charm = charm
        self._metrics_endpoint = MetricsEndpointProvider(
            charm,
            relation_name="metrics-endpoint",
            jobs=[{"static_configs": [{"targets": ["*:9102"]}]}],
        )
        self._logging = LogProxyConsumer(
            charm,
            relation_name="logging",
            log_files=[str(charm_state.flask_access_log), str(charm_state.flask_error_log)],
            container_name=FLASK_CONTAINER_NAME,
        )
        self._grafana_dashboards = GrafanaDashboardProvider(
            charm, relation_name="grafana-dashboard"
        )
        self._charm.framework.observe(
            self._charm.on.statsd_prometheus_exporter_pebble_ready,
            self._on_statsd_prometheus_exporter_pebble_ready,
        )

    def _on_statsd_prometheus_exporter_pebble_ready(self, _event: ops.PebbleReadyEvent) -> None:
        """Handle the statsd-prometheus-exporter-pebble-ready event."""
        container = self._charm.unit.get_container("statsd-prometheus-exporter")
        container.push(
            "/statsd.conf",
            textwrap.dedent(
                """\
                mappings:
                  - match: gunicorn.request.status.*
                    name: flask_response_code
                    labels:
                      status: $1
                  - match: gunicorn.requests
                    name: flask_requests
                  - match: gunicorn.request.duration
                    name: flask_request_duration
                """
            ),
        )
        statsd_layer = ops.pebble.LayerDict(
            summary="statsd exporter layer",
            description="statsd exporter layer",
            services={
                "statsd-prometheus-exporter": {
                    "override": "replace",
                    "summary": "statsd exporter service",
                    "user": "nobody",
                    "command": "/bin/statsd_exporter --statsd.mapping-config=/statsd.conf",
                    "startup": "enabled",
                }
            },
            checks={
                "container-ready": {
                    "override": "replace",
                    "level": "ready",
                    "http": {"url": "http://localhost:9102/metrics"},
                },
            },
        )
        container.add_layer("statsd-prometheus-exporter", statsd_layer, combine=True)
        container.replan()
