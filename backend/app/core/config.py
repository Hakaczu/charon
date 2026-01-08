from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field("postgresql+psycopg://postgres:postgres@db:5432/charon", alias="DB_URL")
    api_port: int = Field(8000, alias="API_PORT")
    admin_token: str = Field("changeme", alias="ADMIN_TOKEN")
    schedule_cron: str = Field("20 12 * * 1-5", alias="SCHEDULE_CRON")
    timezone: str = Field("Europe/Warsaw", alias="TIMEZONE")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    service_version: str = Field("0.1.0", alias="SERVICE_VERSION")
    allowed_origins: List[AnyHttpUrl] | List[str] = Field(["*"], alias="ALLOWED_ORIGINS")


@lru_cache

def get_settings() -> Settings:
    return Settings()
