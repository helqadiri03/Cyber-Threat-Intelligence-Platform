-- Cyber Threats — Cassandra schema (local dev: SimpleStrategy RF=1)
-- Apply: docker compose exec -T cassandra cqlsh -f /schema.cql
-- For multi-node: switch to NetworkTopologyStrategy, e.g.
--   {'class': 'NetworkTopologyStrategy', 'datacenter1': 3}

CREATE KEYSPACE IF NOT EXISTS cyber_threats
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 1
};

USE cyber_threats;

-- Time-series events clustered per sensor, ordered by event_time (newest first)
CREATE TABLE IF NOT EXISTS attack_events (
    sensor_id         text,
    event_time        timestamp,
    attack_type       text,
    source_ip         text,
    destination_port  int,
    flow_duration     bigint,
    label             text,
    confidence        float,
    metadata          map<text, text>,
    PRIMARY KEY ((sensor_id), event_time)
) WITH CLUSTERING ORDER BY (event_time DESC)
  AND comment = 'Network attack events indexed by sensor and time';

-- Secondary index for filtering by attack category
CREATE INDEX IF NOT EXISTS idx_attack_events_attack_type
ON attack_events (attack_type);
