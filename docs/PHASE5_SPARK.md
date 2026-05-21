# Phase 5 — Spark Structured Streaming & AI Inference

## Layout

```
spark/
├── Dockerfile              # apache/spark:3.5.1 + Python deps
├── entrypoint.sh           # spark-submit with connector packages
├── requirements.txt
└── jobs/
    ├── schema.py           # Parquet/Kafka JSON contract (Step 7)
    ├── model_loader.py     # Pipeline + XGB/RF fallback (Steps 17–18)
    ├── sinks.py            # MongoDB, Cassandra, Redis (Steps 20–22)
    └── streaming_inference.py

models/                     # Run: ./scripts/organize_models.sh
├── preprocessing/feature_pipeline/
├── classifiers/xgboost_intrusion_detector/
├── classifiers/random_forest_fallback/
└── label_decoder/string_indexer/
```

## Pipeline flow

1. **Kafka** `cyber_events_raw` → parse JSON with `EVENT_SCHEMA`
2. **Feature pipeline** (saved `PipelineModel`) — StringIndexer → VectorAssembler → StandardScaler
3. **Inference** — XGBoost (`CrossValidatorModel.bestModel`), fallback to Random Forest
4. **Decode** labels via `string_indexer` mapping
5. **Risk score** = 60% confidence + 40% attack severity
6. **Sinks** per micro-batch:
   - Cassandra `attack_events`
   - MongoDB `predictions` + upsert `attacker_profiles`
   - Redis alerts (`alert:*`, counters, `channel:alerts`) when risk ≥ threshold

## Commands

```bash
# Prepare model paths
./scripts/organize_models.sh

# Start streaming job (with full stack)
docker compose up -d spark-streaming kafka-producer

# Logs
docker compose logs -f spark-streaming

# Verify predictions
curl "http://localhost:8000/predictions?page=1&page_size=5"
curl "http://localhost:8000/alerts?limit=5"
```

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_STARTING_OFFSETS` | `earliest` | Use `latest` in production |
| `RISK_ALERT_THRESHOLD` | `80` | Redis alert pub/sub cutoff |
| `STREAM_TRIGGER_INTERVAL` | `10 seconds` | Micro-batch trigger |
| `SPARK_DRIVER_MEMORY` | `2g` | Driver heap |

## Spark packages (auto via entrypoint)

- `spark-sql-kafka-0-10`
- `spark-cassandra-connector`
- `mongo-spark-connector`
