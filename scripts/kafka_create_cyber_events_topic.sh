#!/usr/bin/env bash
# Step 8 — Create cyber_events_raw topic (3 partitions, RF=1, 24h retention).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TOPIC="${KAFKA_TOPIC:-cyber_events_raw}"
PARTITIONS="${KAFKA_TOPIC_PARTITIONS:-3}"
RETENTION_MS="${KAFKA_RETENTION_MS:-86400000}"  # 24 hours

echo "Creating topic: ${TOPIC}"
docker compose exec -T kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create \
  --topic "${TOPIC}" \
  --partitions "${PARTITIONS}" \
  --replication-factor 1 \
  --config retention.ms="${RETENTION_MS}" \
  --if-not-exists

echo ""
echo "Applying retention (idempotent if topic already existed):"
docker compose exec -T kafka kafka-configs \
  --bootstrap-server localhost:29092 \
  --entity-type topics \
  --entity-name "${TOPIC}" \
  --alter \
  --add-config "retention.ms=${RETENTION_MS}"

echo ""
docker compose exec -T kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --describe \
  --topic "${TOPIC}"
