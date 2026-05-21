from starlette.requests import HTTPConnection

from app.services.cassandra import CassandraService
from app.services.mongodb import MongoDBService
from app.services.redis import RedisService
from app.websocket_manager import WebSocketManager


def get_ws_manager(conn: HTTPConnection) -> WebSocketManager:
    return conn.app.state.ws_manager


def get_cassandra(conn: HTTPConnection) -> CassandraService:
    return conn.app.state.cassandra


def get_mongodb(conn: HTTPConnection) -> MongoDBService:
    return conn.app.state.mongodb


def get_redis(conn: HTTPConnection) -> RedisService:
    return conn.app.state.redis



