import json
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.dependencies import get_redis, get_ws_manager
from app.services.redis import RedisService
from app.websocket_manager import WebSocketManager

LOG = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/live")
async def live_feed(
    websocket: WebSocket,
    redis: RedisService = Depends(get_redis),
    manager: WebSocketManager = Depends(get_ws_manager),
) -> None:
    session_id = redis.new_session_id()
    await manager.connect(session_id, websocket)
    await redis.register_session(session_id)

    try:
        await websocket.send_json(
            {"type": "connected", "session_id": session_id, "channel": "channel:alerts"}
        )
        while True:
            # Keep connection alive; client may send pings.
            data = await websocket.receive_text()
            if data.strip().lower() in {"ping", "{\"type\":\"ping\"}"}:
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        LOG.info("Client disconnected session=%s", session_id)
    finally:
        await manager.disconnect(session_id)
        await redis.remove_session(session_id)
