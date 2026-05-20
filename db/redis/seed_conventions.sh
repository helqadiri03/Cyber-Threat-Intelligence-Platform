#!/usr/bin/env bash
# Seeds example Redis keys/channels to verify conventions (safe to re-run).

set -euo pipefail

REDIS_HOST="${REDIS_HOST:-redis}"
TS="$(date +%s%3N)"

redis-cli -h "${REDIS_HOST}" SET "alert:${TS}" \
  '{"attack_type":"Botnet","source_ip":"192.168.1.100","sensor_id":"sensor-01"}' EX 86400

redis-cli -h "${REDIS_HOST}" INCR "counter:attack_type:Botnet"
redis-cli -h "${REDIS_HOST}" INCR "counter:attack_type:Normal"

redis-cli -h "${REDIS_HOST}" SET "dashboard:stats:latest" \
  '{"total_alerts":1,"top_attack":"Botnet","updated_at":"'"$(date -Iseconds)"'"}' EX 30

redis-cli -h "${REDIS_HOST}" HSET "session:demo-ws-001" \
  user_id "demo" connected_at "$(date -Iseconds)" protocol "websocket"
redis-cli -h "${REDIS_HOST}" EXPIRE "session:demo-ws-001" 3600

redis-cli -h "${REDIS_HOST}" PUBLISH "channel:alerts" \
  '{"sensor_id":"sensor-01","attack_type":"Botnet","event_time":"'"$(date -Iseconds)"'"}'

redis-cli -h "${REDIS_HOST}" PUBLISH "channel:predictions" \
  '{"source_ip":"192.168.1.100","predicted_attack":"Botnet","confidence":0.97}'

echo "Redis conventions seeded (alert:${TS}, counters, dashboard cache, demo session)."
