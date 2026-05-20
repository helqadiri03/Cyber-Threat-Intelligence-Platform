from fastapi import Request

from app.services.cassandra import CassandraService
from app.services.mongodb import MongoDBService
from app.services.redis import RedisService
from app.websocket_manager import WebSocketManager


def get_ws_manager(request: Request) -> WebSocketManager:
    return request.app.state.ws_manager


def get_cassandra(request: Request) -> CassandraService:
    return request.app.state.cassandra


def get_mongodb(request: Request) -> MongoDBService:
    return request.app.state.mongodb


def get_redis(request: Request) -> RedisService:
    return request.app.state.redis


def get_ws_manager(request: Request) -> WebSocketManager:
    return request.app.state.ws_manager
