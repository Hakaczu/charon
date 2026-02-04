import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    redis_enabled: bool = Field(True, env="REDIS_ENABLED")
    redis_cache_ttl: int = Field(300, env="REDIS_CACHE_TTL")
    redis_pubsub_channel_rates: str = Field("rates.ingested", env="REDIS_PUBSUB_CHANNEL_RATES")
    redis_pubsub_channel_signals: str = Field("signals.updated", env="REDIS_PUBSUB_CHANNEL_SIGNALS")
    refresh_seconds: int = Field(3600, env="REFRESH_SECONDS")
    nbp_base_url: str = Field("https://api.nbp.pl", env="NBP_BASE_URL")
    enable_rate_limit: bool = Field(False, env="ENABLE_RATE_LIMIT")

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
