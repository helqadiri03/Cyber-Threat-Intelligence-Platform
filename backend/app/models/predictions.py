from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.common import PaginatedResponse


class Prediction(BaseModel):
    id: str | None = None
    source_ip: str
    predicted_attack: str
    confidence: float | None = None
    model_version: str | None = None
    features: dict[str, Any] | None = None
    created_at: datetime


class PredictionsQueryParams(BaseModel):
    source_ip: str | None = None
    attack_type: str | None = Field(default=None, description="Filter by predicted_attack")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


PredictionsPage = PaginatedResponse[Prediction]
