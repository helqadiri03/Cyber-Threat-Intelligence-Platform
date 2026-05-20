#!/usr/bin/env bash
# Pre-pull images used by docker-compose build. Retry on flaky DNS.

set -euo pipefail

IMAGES=(
  python:3.11-slim
  node:20-alpine
  nginx:alpine
  apache/spark:3.5.1
)

for img in "${IMAGES[@]}"; do
  echo "=== Pulling ${img} ==="
  until docker pull "${img}"; do
    echo "Retrying ${img} in 5s..."
    sleep 5
  done
done

echo "All base images ready. Run: docker compose build"
