from fastapi import APIRouter, Depends, Query

from app.dependencies import get_redis
from app.models.alerts import AlertsResponse
from app.services.redis import RedisService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertsResponse)
async def list_alerts(
    limit: int = Query(default=50, ge=1, le=500),
    redis: RedisService = Depends(get_redis),
) -> AlertsResponse:
    """Return recent alerts from Redis keys alert:<timestamp>, newest first."""
    alerts = await redis.get_recent_alerts(limit=limit)
    return AlertsResponse(alerts=alerts, count=len(alerts))
