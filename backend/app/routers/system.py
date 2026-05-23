from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import get_cassandra, get_mongodb, get_redis
from app.services.cassandra import CassandraService
from app.services.mongodb import MongoDBService
from app.services.redis import RedisService

router = APIRouter(tags=["system"])


class ProducerStatusResponse(BaseModel):
    status: str


class ActionResponse(BaseModel):
    status: str
    message: str


@router.post("/system/reset", response_model=ActionResponse)
async def reset_databases(
    cassandra: CassandraService = Depends(get_cassandra),
    mongodb: MongoDBService = Depends(get_mongodb),
    redis: RedisService = Depends(get_redis),
) -> ActionResponse:
    """Reset and delete all data in MongoDB, Cassandra, and Redis."""
    try:
        # 1. Truncate Cassandra telemetry events
        cassandra.truncate_events()
        
        # 2. Clear MongoDB predictions and profiles collections
        await mongodb.clear_database()
        
        # 3. Clear Redis alerts, statistics, and counters
        await redis.clear_redis_data()
        
        return ActionResponse(
            status="success",
            message="All databases (MongoDB, Cassandra, Redis) cleared successfully."
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset system data: {str(exc)}"
        )


@router.get("/producer/status", response_model=ProducerStatusResponse)
async def get_producer_status(
    redis: RedisService = Depends(get_redis)
) -> ProducerStatusResponse:
    """Retrieve the current running status of the data ingestion producer."""
    stat = await redis.get_producer_status()
    return ProducerStatusResponse(status=stat)


@router.post("/producer/start", response_model=ActionResponse)
async def start_producer(
    redis: RedisService = Depends(get_redis)
) -> ActionResponse:
    """Start data ingestion producer flow."""
    await redis.set_producer_status("running")
    return ActionResponse(
        status="success",
        message="Producer control set to active (running)."
    )


@router.post("/producer/stop", response_model=ActionResponse)
async def stop_producer(
    redis: RedisService = Depends(get_redis)
) -> ActionResponse:
    """Stop/pause data ingestion producer flow."""
    await redis.set_producer_status("stopped")
    return ActionResponse(
        status="success",
        message="Producer control set to paused (stopped)."
    )
