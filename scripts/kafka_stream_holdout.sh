#!/usr/bin/env bash
# LEGACY: stream_holdout topic. Prefer Phase 3: ./scripts/phase3_parquet_kafka.sh (cyber_events_raw)
# Create stream_holdout topic, produce parquet rows, and verify consumption.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TOPIC="${KAFKA_TOPIC:-stream_holdout}"
PARTITIONS="${KAFKA_TOPIC_PARTITIONS:-6}"
MAX_ROWS="${MAX_ROWS:-0}"  # 0 = all (~30k rows)

echo "=== 1. Create Kafka topic: ${TOPIC} ==="
docker compose exec -T kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --create \
  --topic "${TOPIC}" \
  --partitions "${PARTITIONS}" \
  --replication-factor 1 \
  --if-not-exists

docker compose exec -T kafka kafka-topics \
  --bootstrap-server localhost:29092 \
  --describe \
  --topic "${TOPIC}"

echo ""
echo "=== 2. Build ingestion image (if needed) ==="
docker compose build kafka-producer

echo ""
echo "=== 3. Produce parquet rows from stream_holdout/ ==="
MAX_ROWS_ARG=()
if [[ "${MAX_ROWS}" != "0" ]]; then
  MAX_ROWS_ARG=(--max-rows "${MAX_ROWS}")
fi

docker compose run --rm kafka-producer produce_stream_holdout.py --topic stream_holdout "${MAX_ROWS_ARG[@]}"

echo ""
echo "=== 4. Verify — consume sample messages ==="
docker compose run --rm kafka-producer verify_stream_holdout.py --topic stream_holdout --max-messages 5

echo ""
echo "=== 5. Topic message count (approximate) ==="
docker compose exec -T kafka kafka-get-offsets \
  --bootstrap-server localhost:29092 \
  --topic "${TOPIC}"

echo ""
echo "Done. Topic '${TOPIC}' is populated from stream_holdout parquet data."
