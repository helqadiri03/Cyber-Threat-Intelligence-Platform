from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EventCreate(BaseModel):
    """Payload for POST /events — maps to Cassandra attack_events."""

    sensor_id: str = Field(..., min_length=1, max_length=128)
    event_time: datetime
    attack_type: str = Field(..., min_length=1, max_length=64)
    source_ip: str = Field(..., min_length=7, max_length=45)
    destination_port: int = Field(..., ge=0, le=65535)
    flow_duration: int = Field(..., ge=0)
    label: str | None = Field(default=None, max_length=64)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("event_time")
    @classmethod
    def ensure_utc_naive_or_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)
        return value


class EventIngestResponse(BaseModel):
    status: str = "accepted"
    sensor_id: str
    event_time: datetime
    message: str = "Event stored in Cassandra"


class EventRecord(EventCreate):
    """Stored event representation."""

    pass


class RawEventPayload(BaseModel):
    """Optional wrapper when clients send { \"event\": { ... } }."""

    event: EventCreate | None = None

    def resolve(self) -> EventCreate:
        if self.event is not None:
            return self.event
        raise ValueError("Missing event payload")
