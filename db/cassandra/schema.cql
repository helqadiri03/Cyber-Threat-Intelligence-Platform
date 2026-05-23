-- Cyber Threats — Cassandra schema (local dev: SimpleStrategy RF=1)
-- Apply: docker compose exec -T cassandra cqlsh -f /schema.cql
-- For multi-node: switch to NetworkTopologyStrategy, e.g.:
--   {'class': 'NetworkTopologyStrategy', 'datacenter1': 3}
--
-- ARCHITECTURE NOTE:
--   Cassandra stores ONLY raw network telemetry — the streaming ingestion layer.
--   AI predictions, confidence scores, and model outputs belong in MongoDB (intelligence layer).
--   This enforces a clean separation of concerns:
--     Cassandra  → raw time-series telemetry  (high write throughput, sensor-partitioned)
--     MongoDB    → enriched intelligence docs  (flexible schema, forensic queries)

CREATE KEYSPACE IF NOT EXISTS cyber_threats
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 1
};

USE cyber_threats;

-- Raw network telemetry events.
-- Partition key: sensor_id  → all events for a sensor in one partition.
-- Clustering key: event_time DESC → most-recent events retrieved first.
-- No AI fields (confidence, attack_type prediction) — those belong to MongoDB.
CREATE TABLE IF NOT EXISTS attack_events (
    sensor_id         TEXT,
    event_time        TIMESTAMP,
    source_ip         TEXT,
    destination_port  INT,
    flow_duration     BIGINT,
    label             TEXT,           -- ground-truth label from dataset (not ML prediction)
    metadata          MAP<TEXT, TEXT>,
    PRIMARY KEY ((sensor_id), event_time)
) WITH CLUSTERING ORDER BY (event_time DESC)
  AND comment = 'Raw network telemetry indexed by sensor, clustered newest-first';
