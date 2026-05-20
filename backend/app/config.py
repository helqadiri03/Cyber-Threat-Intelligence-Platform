from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Cyber Threats API"
    app_version: str = "0.2.0"

    cassandra_hosts: str = "cassandra"
    cassandra_port: int = 9042
    cassandra_keyspace: str = "cyber_threats"

    mongodb_uri: str = "mongodb://admin:changeme@mongodb:27017/?authSource=admin"
    mongodb_database: str = "cyber_intelligence"

    redis_url: str = "redis://redis:6379/0"
    redis_alerts_channel: str = "channel:alerts"
    redis_stats_key: str = "dashboard:stats:latest"
    redis_stats_ttl_seconds: int = 30
    redis_alert_key_prefix: str = "alert:"
    redis_session_key_prefix: str = "session:"

    kafka_bootstrap_servers: str | None = None
    spark_master_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
