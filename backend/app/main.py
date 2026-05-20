import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.common import HealthResponse
from app.routers import alerts, events, predictions, statistics, websocket
from app.services.cassandra import CassandraService
from app.services.mongodb import MongoDBService
from app.services.redis import RedisService
from app.websocket_manager import WebSocketManager

LOG = logging.getLogger(__name__)
settings = get_settings()

cassandra_service = CassandraService(settings)
mongodb_service = MongoDBService(settings)
redis_service = RedisService(settings)
ws_manager = WebSocketManager()


async def _on_alert_message(payload: dict) -> None:
    await ws_manager.broadcast(payload)


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOG.info("Starting application lifespan")
    cassandra_service.connect()
    await mongodb_service.connect()
    await redis_service.connect()

    redis_service.register_alert_handler(_on_alert_message)
    await redis_service.start_pubsub_listener()

    app.state.cassandra = cassandra_service
    app.state.mongodb = mongodb_service
    app.state.redis = redis_service
    app.state.ws_manager = ws_manager

    yield

    await redis_service.stop_pubsub_listener()
    await redis_service.disconnect()
    await mongodb_service.disconnect()
    cassandra_service.disconnect()
    LOG.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(alerts.router)
app.include_router(predictions.router)
app.include_router(statistics.router)
app.include_router(websocket.router)


@app.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    cassandra_ok = mongodb_ok = redis_ok = False
    try:
        cassandra_service.ping()
        cassandra_ok = True
    except Exception:
        pass
    try:
        await mongodb_service.ping()
        mongodb_ok = True
    except Exception:
        pass
    try:
        await redis_service.ping()
        redis_ok = True
    except Exception:
        pass

    status = "ok" if all([cassandra_ok, mongodb_ok, redis_ok]) else "degraded"
    return HealthResponse(
        status=status,
        cassandra="up" if cassandra_ok else "down",
        mongodb="up" if mongodb_ok else "down",
        redis="up" if redis_ok else "down",
        kafka=settings.kafka_bootstrap_servers,
        spark=settings.spark_master_url,
    )
