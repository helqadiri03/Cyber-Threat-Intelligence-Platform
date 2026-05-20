from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.dependencies import get_mongodb, get_redis
from app.models.statistics import AttackTypeCount, StatisticsResponse
from app.services.mongodb import MongoDBService
from app.services.redis import RedisService

router = APIRouter(prefix="/statistics", tags=["statistics"])

CACHE_STALE_SECONDS = 30


@router.get("", response_model=StatisticsResponse)
async def get_statistics(
    redis: RedisService = Depends(get_redis),
    mongodb: MongoDBService = Depends(get_mongodb),
) -> StatisticsResponse:
    """Return cached dashboard stats from Redis, or MongoDB aggregation if cache is stale."""
    cached = await redis.get_cached_statistics()
    now = datetime.now(timezone.utc)

    if cached is not None:
        age = (now - cached.updated_at.replace(tzinfo=timezone.utc)).total_seconds()
        if age <= CACHE_STALE_SECONDS:
            return cached

    agg = await mongodb.aggregate_attack_statistics()
    stats = StatisticsResponse(
        source="mongodb_aggregation",
        total_predictions=agg["total_predictions"],
        total_alerts=cached.total_alerts if cached else 0,
        top_attack=agg["top_attack"],
        attack_breakdown=[
            AttackTypeCount(attack_type=row["attack_type"], count=row["count"])
            for row in agg["attack_breakdown"]
        ],
        updated_at=agg["updated_at"],
    )
    await redis.set_cached_statistics(stats)
    return stats
