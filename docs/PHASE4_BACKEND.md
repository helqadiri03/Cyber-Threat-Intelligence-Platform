# Phase 4 — FastAPI Backend

## Project structure

```
backend/app/
├── main.py              # App factory, lifespan, router registration
├── config.py            # Settings (env-driven)
├── dependencies.py      # FastAPI Depends() accessors
├── websocket_manager.py # Live WebSocket broadcast hub
├── models/              # Pydantic schemas
│   ├── events.py
│   ├── alerts.py
│   ├── predictions.py
│   └── statistics.py
├── routers/
│   ├── events.py        # POST /events
│   ├── alerts.py        # GET /alerts
│   ├── predictions.py   # GET /predictions
│   ├── statistics.py    # GET /statistics
│   └── websocket.py     # WS /ws/live
└── services/            # DB singletons
    ├── cassandra.py     # cassandra-driver (sync)
    ├── mongodb.py       # motor (async)
    └── redis.py         # redis.asyncio (async)
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | DB connectivity status |
| POST | `/events` | Ingest raw event → Cassandra |
| GET | `/alerts` | Recent Redis alerts |
| GET | `/predictions` | MongoDB predictions (paginated, filters) |
| GET | `/statistics` | Redis cache or MongoDB aggregation |
| WS | `/ws/live` | Live alert stream via Redis pub/sub |

## Test commands

```bash
# Connection managers (Step 11)
docker compose exec backend python scripts/test_connections.py

# API smoke test (Steps 12–14)
./scripts/test_backend_api.sh

# Publish test alert → WebSocket clients
docker compose exec redis redis-cli PUBLISH channel:alerts \
  '{"sensor_id":"s1","attack_type":"DDoS","source_ip":"10.0.0.1"}'
```

## POST /events example

```json
{
  "sensor_id": "sensor-01",
  "event_time": "2026-05-20T12:00:00",
  "attack_type": "Botnet",
  "source_ip": "192.168.1.50",
  "destination_port": 443,
  "flow_duration": 1200,
  "label": "Botnet",
  "confidence": 0.91,
  "metadata": {"source": "api"}
}
```
