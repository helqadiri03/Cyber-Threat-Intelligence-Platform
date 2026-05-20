#!/usr/bin/env bash
# Phase 2 — Configure Cassandra, MongoDB, and Redis conventions.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Load .env if present
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

MONGO_USER="${MONGO_ROOT_USER:-admin}"
MONGO_PASS="${MONGO_ROOT_PASSWORD:-changeme}"
CASSANDRA_KS="${CASSANDRA_KEYSPACE:-cyber_threats}"

echo "=== Step 4: Cassandra ==="
docker compose cp db/cassandra/schema.cql cassandra:/schema.cql
docker compose exec -T cassandra cqlsh -f /schema.cql
docker compose exec -T cassandra cqlsh -e "USE ${CASSANDRA_KS}; DESCRIBE TABLE attack_events;"
docker compose exec -T cassandra cqlsh -e \
  "SELECT index_name FROM system_schema.indexes WHERE keyspace_name='${CASSANDRA_KS}' AND table_name='attack_events';"

echo ""
echo "=== Step 5: MongoDB (cyber_intelligence) ==="
docker compose cp db/mongodb/init.js mongodb:/init.js
docker compose exec -T mongodb mongosh \
  -u "${MONGO_USER}" -p "${MONGO_PASS}" \
  --authenticationDatabase admin \
  /init.js
docker compose exec -T mongodb mongosh \
  -u "${MONGO_USER}" -p "${MONGO_PASS}" \
  --authenticationDatabase admin \
  --eval 'db = db.getSiblingDB("cyber_intelligence"); print("Collections:", db.getCollectionNames()); print("predictions indexes:", db.predictions.getIndexes().map(i => i.name));'

echo ""
echo "=== Step 6: Redis conventions ==="
docker compose cp db/redis/seed_conventions.sh redis:/seed_conventions.sh
docker compose exec -T redis sh -c "REDIS_HOST=127.0.0.1 sh /seed_conventions.sh"
echo "Key patterns documented in: db/redis/CONVENTIONS.md"
docker compose exec -T redis redis-cli GET "dashboard:stats:latest"

echo ""
echo "Database setup complete."
