# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Provide the Observability class to represent the observability stack for charms."""
import pathlib
import typing

import ops
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider


class ObservabilityCharmState(typing.Protocol):
    """CharmState interface required by Observability class.

    Attrs:
        application_log_file: the path to the application's main log file.
        application_error_log_file: the path to the application's error error file.
    """

    @property
    def application_log_file(self) -> pathlib.Path:
        """Return the path to the application's main log file.

        Returns:
            The path to the application's main log file.
        """

    @property
    def application_error_log_file(self) -> pathlib.Path:
        """Return the path to the application's error log file.

        Returns:
            The path to the application's error log file.
        """


class Observability(ops.Object):  # pylint: disable=too-few-public-methods
    """A class representing the observability stack for Flask application."""

    def __init__(
        self, charm: ops.CharmBase, charm_state: ObservabilityCharmState, container_name: str
    ):
        """Initialize a new instance of the Observability class.

        Args:
            charm: The charm object that the Observability instance belongs to.
            charm_state: The state of the charm that the Observability instance belongs to.
            container_name: The name of the application container.
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
            log_files=[
                str(charm_state.application_log_file),
                str(charm_state.application_error_log_file),
            ],
            container_name=container_name,
        )
        self._grafana_dashboards = GrafanaDashboardProvider(
            charm, relation_name="grafana-dashboard"
        )
