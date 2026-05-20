from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class MessageResponse(BaseModel):
    status: str = "ok"
    message: str


class HealthResponse(BaseModel):
    status: str
    cassandra: str
    mongodb: str
    redis: str
    kafka: str | None = None
    spark: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool


class TimestampedModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
