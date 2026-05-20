# Redis Key & Pub/Sub Conventions

All backend services, Spark jobs, and WebSocket handlers **must** use these exact patterns.

## Key patterns

| Pattern | Type | Purpose | Example |
|---------|------|---------|---------|
| `alert:<timestamp>` | String (JSON) | Single real-time alert payload | `alert:1716123456789` |
| `counter:attack_type:<type>` | String (integer) | Per-attack-type event counter | `counter:attack_type:Botnet` |
| `dashboard:stats:latest` | String (JSON) | Cached dashboard summary metrics | `dashboard:stats:latest` |
| `session:<id>` | Hash | Active WebSocket session state | `session:ws-abc123` |

### Optional extensions (use consistently if needed)

| Pattern | Type | Purpose |
|---------|------|---------|
| `prediction:latest:<source_ip>` | String (JSON) | Latest inference for an IP |
| `profile:<source_ip>` | String (JSON) | Cached attacker profile snapshot |
| `lock:ingest:<sensor_id>` | String | Short-lived ingest dedup lock (SET NX EX) |

## Pub/Sub channels

| Channel | Publishers | Subscribers | Payload |
|---------|------------|-------------|---------|
| `channel:alerts` | Spark streaming, ingestion | Backend WebSocket bridge | JSON alert events |
| `channel:predictions` | ML inference service | Backend API, dashboard | JSON prediction results |

## Data types & TTL guidance

- **Alerts:** `SET alert:<ts> <json> EX 86400` (24h retention per alert key)
- **Counters:** `INCR counter:attack_type:<type>` — no TTL (monotonic)
- **Dashboard cache:** `SET dashboard:stats:latest <json> EX 30` (refresh every 30s)
- **Sessions:** `HSET session:<id> ...` + `EXPIRE session:<id> 3600` (1h idle timeout)

## Example commands

```bash
# Alert
redis-cli SET "alert:1716123456789" '{"attack_type":"Botnet","source_ip":"10.0.0.5"}' EX 86400

# Counter
redis-cli INCR "counter:attack_type:Botnet"

# Dashboard cache
redis-cli SET "dashboard:stats:latest" '{"total_alerts":42,"top_attack":"Botnet"}' EX 30

# Session
redis-cli HSET "session:ws-abc123" user_id "u1" connected_at "2026-05-20T12:00:00Z"
redis-cli EXPIRE "session:ws-abc123" 3600

# Publish
redis-cli PUBLISH "channel:alerts" '{"sensor_id":"s1","attack_type":"DDoS"}'
redis-cli PUBLISH "channel:predictions" '{"source_ip":"10.0.0.5","predicted_attack":"Botnet"}'
```
