from fastapi import APIRouter, Depends, Query

from app.dependencies import get_mongodb
from app.models.common import PaginatedResponse
from app.models.predictions import Prediction
from app.services.mongodb import MongoDBService

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("", response_model=PaginatedResponse[Prediction])
async def list_predictions(
    source_ip: str | None = Query(default=None),
    attack_type: str | None = Query(default=None, description="Filter by predicted_attack"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    mongodb: MongoDBService = Depends(get_mongodb),
) -> PaginatedResponse[Prediction]:
    items, total = await mongodb.list_predictions(
        source_ip=source_ip,
        attack_type=attack_type,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )
