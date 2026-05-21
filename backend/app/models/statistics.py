from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AttackTypeCount(BaseModel):
    attack_type: str
    count: int


class TopIpEntry(BaseModel):
    source_ip: str
    count: int


class TimelineBucket(BaseModel):
    timestamp: datetime
    count: int


class StatisticsResponse(BaseModel):
    source: str = Field(description="redis_cache | mongodb_aggregation")
    total_predictions: int = 0
    total_alerts: int = 0
    top_attack: str | None = None
    attack_breakdown: list[AttackTypeCount] = Field(default_factory=list)
    top_ips: list[TopIpEntry] = Field(default_factory=list)
    timeline: list[TimelineBucket] = Field(default_factory=list)
    updated_at: datetime
    cache_ttl_seconds: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
