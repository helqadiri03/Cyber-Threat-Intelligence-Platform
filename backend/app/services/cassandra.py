"""Cassandra connection singleton (cassandra-driver, sync with retry policy)."""

from __future__ import annotations

import logging
from typing import Any

from cassandra.cluster import Cluster, Session
from cassandra.policies import FallthroughRetryPolicy, RoundRobinPolicy
from cassandra.query import PreparedStatement, dict_factory

from app.config import Settings
from app.models.events import EventCreate

LOG = logging.getLogger(__name__)

INSERT_EVENT_CQL = """
INSERT INTO attack_events (
    sensor_id, event_time, attack_type, source_ip,
    destination_port, flow_duration, label, confidence, metadata
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class CassandraService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cluster: Cluster | None = None
        self._session: Session | None = None
        self._insert_stmt: PreparedStatement | None = None

    @property
    def is_connected(self) -> bool:
        return self._session is not None and not self._session.is_shutdown

    def connect(self) -> None:
        if self.is_connected:
            return

        hosts = [h.strip() for h in self._settings.cassandra_hosts.split(",") if h.strip()]
        LOG.info("Connecting to Cassandra at %s:%s", hosts, self._settings.cassandra_port)

        self._cluster = Cluster(
            contact_points=hosts,
            port=self._settings.cassandra_port,
            load_balancing_policy=RoundRobinPolicy(),
            default_retry_policy=FallthroughRetryPolicy(),
            connect_timeout=15,
        )
        self._session = self._cluster.connect(self._settings.cassandra_keyspace)
        self._session.row_factory = dict_factory
        self._insert_stmt = self._session.prepare(INSERT_EVENT_CQL)
        LOG.info("Cassandra connected (keyspace=%s)", self._settings.cassandra_keyspace)

    def disconnect(self) -> None:
        if self._session is not None:
            self._session.shutdown()
            self._session = None
        if self._cluster is not None:
            self._cluster.shutdown()
            self._cluster = None
        self._insert_stmt = None
        LOG.info("Cassandra disconnected")

    def ping(self) -> bool:
        if not self.is_connected:
            self.connect()
        assert self._session is not None
        self._session.execute("SELECT now() FROM system.local")
        return True

    def insert_event(self, event: EventCreate) -> None:
        if not self.is_connected:
            self.connect()
        assert self._session is not None and self._insert_stmt is not None

        self._session.execute(
            self._insert_stmt,
            (
                event.sensor_id,
                event.event_time,
                event.attack_type,
                event.source_ip,
                event.destination_port,
                event.flow_duration,
                event.label,
                event.confidence,
                event.metadata or {},
            ),
        )

    def fetch_recent_events(self, sensor_id: str, limit: int = 10) -> list[dict[str, Any]]:
        if not self.is_connected:
            self.connect()
        assert self._session is not None
        rows = self._session.execute(
            """
            SELECT sensor_id, event_time, attack_type, source_ip, destination_port,
                   flow_duration, label, confidence, metadata
            FROM attack_events
            WHERE sensor_id = %s
            LIMIT %s
            """,
            (sensor_id, limit),
        )
        return list(rows)
