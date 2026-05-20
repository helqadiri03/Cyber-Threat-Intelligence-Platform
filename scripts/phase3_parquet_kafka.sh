#!/usr/bin/env bash
# Phase 3 — inspect Parquet, create topic, verify producer (Steps 7–9).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "========== Step 7: Inspect Parquet & write schema contract =========="
docker compose build kafka-producer
docker compose run --rm \
  -v "${ROOT}/docs:/app/docs" \
  -v "${ROOT}/ingestion:/app/ingestion_out" \
  -v "${ROOT}/models:/app/models:ro" \
  kafka-producer inspect_parquet.py \
    --output-json /app/ingestion_out/schema_contract.json \
    --output-md /app/docs/PARQUET_SCHEMA.md \
    --selected-features /app/models/selected_features.pkl

echo ""
echo "========== Step 8: Create Kafka topic cyber_events_raw =========="
./scripts/kafka_create_cyber_events_topic.sh

echo ""
echo "========== Step 9: Test producer (100 rows, no loop) =========="
docker compose run --rm -e PRODUCER_LOOP=false kafka-producer produce_cyber_events.py \
  --max-rows 100 --sleep-seconds 0.001

echo ""
echo "========== Verify offsets =========="
docker compose exec -T kafka kafka-get-offsets \
  --bootstrap-server localhost:29092 \
  --topic cyber_events_raw

echo ""
echo "Phase 3 setup complete. Start continuous stream: docker compose up -d kafka-producer"
