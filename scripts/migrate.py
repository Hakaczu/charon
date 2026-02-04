"""
One-off migration script.
Run inside container: python scripts/migrate.py
Requires DATABASE_URL env (Postgres or SQLite).
"""
from __future__ import annotations

import asyncio
import os
from typing import List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def make_engine_url(url: str) -> str:
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite://"):
        if ":memory:" in url or url.startswith("sqlite:///"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return f"sqlite+aiosqlite:///{url.split('sqlite:///')[-1]}"
    return url


DDL_STATEMENTS: List[str] = [
    # currencies
    """
    CREATE TABLE IF NOT EXISTS currencies (
        code VARCHAR(8) PRIMARY KEY,
        name VARCHAR(128) NOT NULL,
        source VARCHAR(32) NOT NULL DEFAULT 'NBP'
    );
    """,
    # rates
    """
    CREATE TABLE IF NOT EXISTS rates (
        id SERIAL PRIMARY KEY,
        code VARCHAR(8) NOT NULL,
        rate_mid NUMERIC(18,6) NOT NULL,
        effective_date DATE NOT NULL,
        fetched_at TIMESTAMP DEFAULT now(),
        source VARCHAR(32) NOT NULL DEFAULT 'NBP'
    );
    """,
    # gold_prices
    """
    CREATE TABLE IF NOT EXISTS gold_prices (
        id SERIAL PRIMARY KEY,
        price NUMERIC(18,6) NOT NULL,
        effective_date DATE NOT NULL,
        fetched_at TIMESTAMP DEFAULT now(),
        source VARCHAR(32) NOT NULL DEFAULT 'NBP',
        CONSTRAINT uq_gold_date UNIQUE (effective_date)
    );
    """,
    # jobs_log
    """
    CREATE TABLE IF NOT EXISTS jobs_log (
        id SERIAL PRIMARY KEY,
        job_type VARCHAR(32) NOT NULL,
        status VARCHAR(16) NOT NULL,
        started_at TIMESTAMP DEFAULT now(),
        finished_at TIMESTAMP,
        rows_written INTEGER DEFAULT 0,
        error VARCHAR(512)
    );
    """,
    # signals
    """
    CREATE TABLE IF NOT EXISTS signals (
        id SERIAL PRIMARY KEY,
        asset_code VARCHAR(16) NOT NULL,
        signal VARCHAR(8) NOT NULL,
        macd NUMERIC(18,6) NOT NULL,
        signal_line NUMERIC(18,6) NOT NULL,
        histogram NUMERIC(18,6) NOT NULL,
        generated_at TIMESTAMP DEFAULT now(),
        horizon_days INTEGER DEFAULT 0
    );
    """,
    # analysis_snapshots
    """
    CREATE TABLE IF NOT EXISTS analysis_snapshots (
        id SERIAL PRIMARY KEY,
        asset_code VARCHAR(16) NOT NULL,
        window_name VARCHAR(32) NOT NULL,
        stats TEXT NOT NULL,
        generated_at TIMESTAMP DEFAULT now()
    );
    """,
    # backfill columns if table existed already
    "ALTER TABLE IF EXISTS currencies ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT 'NBP';",
    "ALTER TABLE IF EXISTS rates ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT 'NBP';",
    "ALTER TABLE IF EXISTS rates DROP COLUMN IF EXISTS currency_id;",
    "ALTER TABLE IF EXISTS rates ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMP DEFAULT now();",
    "ALTER TABLE IF EXISTS rates ADD COLUMN IF NOT EXISTS rate_mid NUMERIC(18,6);",
    "ALTER TABLE IF EXISTS rates ADD COLUMN IF NOT EXISTS effective_date DATE;",
    "ALTER TABLE IF EXISTS rates ADD COLUMN IF NOT EXISTS code VARCHAR(8);",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_rate_code_date ON rates (code, effective_date);",
    # index
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_rate_code_date ON rates (code, effective_date);",
]


async def main() -> None:
    url = make_engine_url(os.environ["DATABASE_URL"])
    engine = create_async_engine(url, echo=False, future=True)
    async with engine.begin() as conn:
        for stmt in DDL_STATEMENTS:
            await conn.execute(text(stmt))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
