from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Alert(BaseModel):
    alert_id: str
    timestamp: datetime
    attack_type: str | None = None
    source_ip: str | None = None
    sensor_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AlertsResponse(BaseModel):
    alerts: list[Alert]
    count: int
