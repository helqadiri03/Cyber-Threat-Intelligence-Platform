"""Manages live WebSocket connections and broadcasts alert messages."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

LOG = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        return len(self._connections)

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[session_id] = websocket
        LOG.info("WebSocket connected session=%s (active=%s)", session_id, self.active_count)

    async def disconnect(self, session_id: str) -> None:
        async with self._lock:
            self._connections.pop(session_id, None)
        LOG.info("WebSocket disconnected session=%s (active=%s)", session_id, self.active_count)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        message = json.dumps({"type": "alert", "data": payload})
        async with self._lock:
            targets = list(self._connections.items())

        stale: list[str] = []
        for session_id, websocket in targets:
            try:
                await websocket.send_text(message)
            except Exception:
                stale.append(session_id)

        for session_id in stale:
            await self.disconnect(session_id)
