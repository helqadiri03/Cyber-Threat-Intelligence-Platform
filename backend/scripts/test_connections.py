#!/usr/bin/env python3
"""Step 11 — Test database connection managers in isolation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.services.cassandra import CassandraService
from app.services.mongodb import MongoDBService
from app.services.redis import RedisService


async def test_mongodb(service: MongoDBService) -> None:
    await service.connect()
    await service.ping()
    total = await service.db.predictions.count_documents({})
    print(f"[mongodb] OK — predictions count={total}")


async def test_redis(service: RedisService) -> None:
    await service.connect()
    await service.ping()
    alerts = await service.get_recent_alerts(limit=3)
    print(f"[redis] OK — sample alerts={len(alerts)}")


def test_cassandra(service: CassandraService) -> None:
    service.connect()
    service.ping()
    rows = service.fetch_recent_events("sensor-test", limit=1)
    print(f"[cassandra] OK — sample query rows={len(rows)}")


async def main() -> int:
    settings = get_settings()
    cassandra = CassandraService(settings)
    mongodb = MongoDBService(settings)
    redis = RedisService(settings)

    errors = 0
    try:
        test_cassandra(cassandra)
    except Exception as exc:
        print(f"[cassandra] FAIL — {exc}")
        errors += 1
    finally:
        cassandra.disconnect()

    try:
        await test_mongodb(mongodb)
    except Exception as exc:
        print(f"[mongodb] FAIL — {exc}")
        errors += 1
    finally:
        await mongodb.disconnect()

    try:
        await test_redis(redis)
    except Exception as exc:
        print(f"[redis] FAIL — {exc}")
        errors += 1
    finally:
        await redis.disconnect()

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
