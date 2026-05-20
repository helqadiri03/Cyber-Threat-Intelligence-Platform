import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_cassandra
from app.models.events import EventCreate, EventIngestResponse
from app.services.cassandra import CassandraService

LOG = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    event: EventCreate,
    cassandra: CassandraService = Depends(get_cassandra),
) -> EventIngestResponse:
    """Lightweight ingestion — validate and persist raw event to Cassandra only."""
    try:
        await asyncio.to_thread(cassandra.insert_event, event)
    except Exception as exc:
        LOG.exception("Failed to insert event for sensor=%s", event.sensor_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cassandra write failed: {exc}",
        ) from exc

    return EventIngestResponse(sensor_id=event.sensor_id, event_time=event.event_time)
