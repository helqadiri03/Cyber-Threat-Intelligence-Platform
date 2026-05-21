"""Redis connection singleton (redis.asyncio — maintained successor to aioredis)."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from app.config import Settings
from app.models.alerts import Alert
from app.models.statistics import AttackTypeCount, StatisticsResponse

LOG = logging.getLogger(__name__)

AlertHandler = Callable[[dict[str, Any]], Awaitable[None]]


class RedisService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Redis | None = None
        self._pubsub: PubSub | None = None
        self._listener_task: asyncio.Task | None = None
        self._alert_handlers: list[AlertHandler] = []

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("Redis is not connected")
        return self._client

    async def connect(self) -> None:
        if self.is_connected:
            return
        LOG.info("Connecting to Redis at %s", self._settings.redis_url)
        self._client = Redis.from_url(
            self._settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await self._client.ping()
        LOG.info("Redis connected")

    async def disconnect(self) -> None:
        await self.stop_pubsub_listener()
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            LOG.info("Redis disconnected")

    async def ping(self) -> bool:
        if not self.is_connected:
            await self.connect()
        await self.client.ping()
        return True

    def register_alert_handler(self, handler: AlertHandler) -> None:
        self._alert_handlers.append(handler)

    async def start_pubsub_listener(self) -> None:
        if self._listener_task is not None:
            return
        if not self.is_connected:
            await self.connect()

        self._pubsub = self.client.pubsub()
        await self._pubsub.subscribe(self._settings.redis_alerts_channel)
        self._listener_task = asyncio.create_task(self._listen_alerts())
        LOG.info("Redis pub/sub listening on %s", self._settings.redis_alerts_channel)

    async def stop_pubsub_listener(self) -> None:
        if self._listener_task is not None:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None

        if self._pubsub is not None:
            await self._pubsub.unsubscribe(self._settings.redis_alerts_channel)
            await self._pubsub.aclose()
            self._pubsub = None

    async def _listen_alerts(self) -> None:
        assert self._pubsub is not None
        try:
            async for message in self._pubsub.listen():
                if message is None or message.get("type") != "message":
                    continue
                raw = message.get("data")
                try:
                    payload = json.loads(raw) if isinstance(raw, str) else raw
                except json.JSONDecodeError:
                    payload = {"raw": raw}
                for handler in self._alert_handlers:
                    await handler(payload)
        except asyncio.CancelledError:
            LOG.info("Redis pub/sub listener stopped")
            raise

    async def register_session(self, session_id: str, metadata: dict[str, str] | None = None) -> None:
        key = f"{self._settings.redis_session_key_prefix}{session_id}"
        data = {
            "session_id": session_id,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }
        await self.client.hset(key, mapping=data)
        await self.client.expire(key, 3600)

    async def remove_session(self, session_id: str) -> None:
        key = f"{self._settings.redis_session_key_prefix}{session_id}"
        await self.client.delete(key)

    async def get_recent_alerts(self, limit: int = 50) -> list[Alert]:
        prefix = self._settings.redis_alert_key_prefix
        keys = [key async for key in self.client.scan_iter(match=f"{prefix}*", count=200)]
        keys.sort(reverse=True)
        keys = keys[:limit]

        alerts: list[Alert] = []
        for key in keys:
            raw = await self.client.get(key)
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"raw": raw}

            ts_str = key.removeprefix(prefix)
            try:
                ts_raw = int(ts_str)
                # Keys may use milliseconds (13+ digits) or seconds (10 digits)
                ts = (
                    datetime.fromtimestamp(ts_raw / 1000.0, tz=timezone.utc)
                    if ts_raw > 10_000_000_000
                    else datetime.fromtimestamp(ts_raw, tz=timezone.utc)
                )
            except ValueError:
                ts = datetime.now(timezone.utc)

            alerts.append(
                Alert(
                    alert_id=key,
                    timestamp=ts,
                    attack_type=payload.get("attack_type"),
                    source_ip=payload.get("source_ip"),
                    sensor_id=payload.get("sensor_id"),
                    payload=payload,
                )
            )

        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return alerts

    async def get_total_alerts(self) -> int:
        """Calculate the total number of alerts using the attack_type counters."""
        total = 0
        keys = [key async for key in self.client.scan_iter(match="counter:attack_type:*")]
        if not keys:
            return 0
        
        values = await self.client.mget(keys)
        for v in values:
            if v:
                try:
                    total += int(v)
                except ValueError:
                    pass
        return total

    async def get_cached_statistics(self) -> StatisticsResponse | None:
        raw = await self.client.get(self._settings.redis_stats_key)
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None

        ttl = await self.client.ttl(self._settings.redis_stats_key)
        updated_raw = data.get("updated_at")
        data["source"] = "redis_cache"
        data["cache_ttl_seconds"] = ttl if ttl and ttl > 0 else None
        if isinstance(updated_raw, str):
            data["updated_at"] = updated_raw.replace("Z", "+00:00")
        
        # Handle legacy attack_breakdown format if it was a dict
        if isinstance(data.get("attack_breakdown"), dict):
            data["attack_breakdown"] = [
                {"attack_type": k, "count": int(v)}
                for k, v in data["attack_breakdown"].items()
            ]

        try:
            return StatisticsResponse.model_validate(data)
        except Exception as e:
            LOG.error("Failed to parse cached statistics: %s", e)
            return None

    async def set_cached_statistics(self, stats: StatisticsResponse) -> None:
        payload = stats.model_dump(mode="json")
        await self.client.set(
            self._settings.redis_stats_key,
            json.dumps(payload),
            ex=self._settings.redis_stats_ttl_seconds,
        )

    @staticmethod
    def new_session_id() -> str:
        return f"ws-{uuid.uuid4().hex[:12]}"
