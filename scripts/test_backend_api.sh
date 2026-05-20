#!/usr/bin/env bash
# Smoke-test Phase 4 FastAPI endpoints.

set -euo pipefail

API="${API_BASE:-http://localhost:8000}"

echo "=== Health ==="
curl -s "${API}/health" | python3 -m json.tool

echo ""
echo "=== POST /events ==="
curl -s -X POST "${API}/events" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "sensor-01",
    "event_time": "2026-05-20T12:00:00",
    "attack_type": "Botnet",
    "source_ip": "192.168.1.50",
    "destination_port": 443,
    "flow_duration": 1200,
    "label": "Botnet",
    "confidence": 0.91,
    "metadata": {"source": "api-test"}
  }' | python3 -m json.tool

echo ""
echo "=== GET /alerts ==="
curl -s "${API}/alerts?limit=5" | python3 -m json.tool

echo ""
echo "=== GET /predictions ==="
curl -s "${API}/predictions?page=1&page_size=5" | python3 -m json.tool

echo ""
echo "=== GET /statistics ==="
curl -s "${API}/statistics" | python3 -m json.tool

echo ""
echo "API smoke test complete."
