from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.common import PaginatedResponse


class Prediction(BaseModel):
    id: str | None = None
    source_ip: str
    predicted_attack: str
    # ML probability in [0, 1] — multiply by 100 for percentage display
    confidence: float | None = None
    # Composite risk score in [0, 100]: confidence*100*0.6 + severity_weight*0.4
    risk_score: float | None = None
    # End-to-end inference latency in milliseconds
    prediction_latency_ms: int | None = None
    model_version: str | None = None
    features: dict[str, Any] | None = None
    created_at: datetime


class PredictionsQueryParams(BaseModel):
    source_ip: str | None = None
    attack_type: str | None = Field(default=None, description="Filter by predicted_attack")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


PredictionsPage = PaginatedResponse[Prediction]
