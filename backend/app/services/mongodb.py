"""MongoDB connection singleton (motor async driver)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import Settings
from app.models.predictions import Prediction

LOG = logging.getLogger(__name__)


class MongoDBService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise RuntimeError("MongoDB is not connected")
        return self._db

    async def connect(self) -> None:
        if self.is_connected:
            return
        LOG.info("Connecting to MongoDB (%s)", self._settings.mongodb_database)
        self._client = AsyncIOMotorClient(self._settings.mongodb_uri)
        self._db = self._client[self._settings.mongodb_database]
        await self._client.admin.command("ping")
        LOG.info("MongoDB connected (db=%s)", self._settings.mongodb_database)

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            LOG.info("MongoDB disconnected")

    async def ping(self) -> bool:
        if not self.is_connected:
            await self.connect()
        await self._client.admin.command("ping")  # type: ignore[union-attr]
        return True

    async def list_predictions(
        self,
        *,
        source_ip: str | None = None,
        attack_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Prediction], int]:
        query: dict[str, Any] = {}
        if source_ip:
            query["source_ip"] = source_ip
        if attack_type:
            query["predicted_attack"] = attack_type

        collection = self.db.predictions
        total = await collection.count_documents(query)
        skip = (page - 1) * page_size
        cursor = (
            collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )

        items: list[Prediction] = []
        async for doc in cursor:
            items.append(
                Prediction(
                    id=str(doc.get("_id")),
                    source_ip=doc["source_ip"],
                    predicted_attack=doc["predicted_attack"],
                    confidence=doc.get("confidence"),
                    model_version=doc.get("model_version"),
                    features=doc.get("features"),
                    created_at=doc.get("created_at") or datetime.now(timezone.utc),
                )
            )
        return items, total

    async def aggregate_attack_statistics(self) -> dict[str, Any]:
        pipeline = [
            {"$group": {"_id": "$predicted_attack", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        breakdown = []
        total = 0
        async for row in self.db.predictions.aggregate(pipeline):
            count = int(row["count"])
            total += count
            breakdown.append({"attack_type": row["_id"], "count": count})

        top_attack = breakdown[0]["attack_type"] if breakdown else None
        return {
            "total_predictions": total,
            "top_attack": top_attack,
            "attack_breakdown": breakdown,
            "updated_at": datetime.now(timezone.utc),
        }
