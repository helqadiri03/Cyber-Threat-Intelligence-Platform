# Phase 3 — Parquet Data Source & Kafka Pipeline

## Status overview

| Step | Requirement | Status | Notes |
|------|-------------|--------|-------|
| **7** | Inspect Parquet (columns, types, rows, nulls) | ✅ Done | `ingestion/inspect_parquet.py` |
| **7** | Compare vs selected features metadata | ✅ Done | Uses `models/selected_features.pkl` |
| **7** | Document schema contract | ✅ Done | `ingestion/schema_contract.json`, `docs/PARQUET_SCHEMA.md` |
| **8** | Topic `cyber_events_raw` | ✅ Done | 3 partitions, RF=1, 24h retention |
| **8** | Topic `stream_holdout` (earlier) | ⚠️ Legacy | Kept for old tests; use `cyber_events_raw` going forward |
| **9** | PyArrow batch reads | ✅ Done | `produce_cyber_events.py` |
| **9** | JSON per row | ✅ Done | |
| **9** | Configurable sleep | ✅ Done | `PRODUCER_SLEEP_SECONDS` |
| **9** | Loop mode | ✅ Done | `PRODUCER_LOOP` / `--loop` |
| **9** | Logging (rate, errors) | ✅ Done | stdlib `logging` |
| **9** | Standalone Compose service (auto-start) | ✅ Done | `kafka-producer` + `kafka-init` |

## Commands

```bash
# Full Phase 3 setup (inspect + topic + test publish)
./scripts/phase3_parquet_kafka.sh

# Start producer with the stack
docker compose up -d kafka-init kafka-producer

# Tune simulation speed
PRODUCER_SLEEP_SECONDS=0.1 PRODUCER_LOOP=true docker compose up -d kafka-producer
```

## Earlier work superseded

- `ingestion/produce_stream_holdout.py` → topic `stream_holdout` (manual / one-shot)
- `scripts/kafka_stream_holdout.sh` → use `phase3_parquet_kafka.sh` + `cyber_events_raw` instead
