from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import get_settings

settings = get_settings()

# Convert sync URL to async if needed
url = settings.database_url
if url.startswith("postgresql+psycopg2://"):
    async_url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
elif url.startswith("postgresql://"):
    async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif url.startswith("sqlite://"):
    if ":memory:" in url or url.startswith("sqlite:///"):
        async_url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    else:
        async_url = f"sqlite+aiosqlite:///{url.split('sqlite:///')[-1]}"
else:
    async_url = url

engine = create_async_engine(async_url, future=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


@asynccontextmanager
async def session_scope():
    async with SessionLocal() as session:
        yield session
