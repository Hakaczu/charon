from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .config import get_settings
from .db import Base, engine, session_scope
from .cache import publish
from .models import Currency, Rate, GoldPrice, JobLog, JobStatus
from .nbp_client import NBPClient

logger = logging.getLogger(__name__)
settings = get_settings()


def utc_now_naive() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


async def ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE IF EXISTS rates ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMP DEFAULT now();"))
        await conn.execute(text("ALTER TABLE IF EXISTS rates DROP COLUMN IF EXISTS currency_id;"))


def daterange_chunks(start: dt.date, end: dt.date, chunk: int = 90):
    cur = start
    while cur <= end:
        nxt = min(cur + dt.timedelta(days=chunk - 1), end)
        yield cur, nxt
        cur = nxt + dt.timedelta(days=1)


async def import_rates(session, client: NBPClient, start: dt.date, end: dt.date) -> int:
    rows = 0
    for chunk_start, chunk_end in daterange_chunks(start, end, 90):
        data = await client.fetch_rates(chunk_start, chunk_end)
        for day in data:
            effective_date = dt.datetime.strptime(day["effectiveDate"], "%Y-%m-%d").date()
            for item in day.get("rates", []):
                code = item.get("code")
                rate_mid = item.get("mid")
                if code is None or rate_mid is None:
                    continue
                name = item.get("currency") or code
                # Upsert currency
                inserted = 0
                if session.bind.dialect.name == "postgresql":
                    stmt_cur = pg_insert(Currency).values(code=code, name=name, source="NBP").on_conflict_do_nothing(
                        index_elements=[Currency.code]
                    )
                    res_cur = await session.execute(stmt_cur)
                    inserted += res_cur.rowcount or 0
                else:
                    existing_cur = await session.get(Currency, code)
                    if not existing_cur:
                        session.add(Currency(code=code, name=name, source="NBP"))
                        inserted += 1
                # Upsert rate
                if session.bind.dialect.name == "postgresql":
                    stmt_rate = (
                        pg_insert(Rate)
                        .values(code=code, rate_mid=rate_mid, effective_date=effective_date, source="NBP")
                        .on_conflict_do_nothing(index_elements=[Rate.code, Rate.effective_date])
                    )
                    res_rate = await session.execute(stmt_rate)
                    inserted += res_rate.rowcount or 0
                else:
                    existing_rate = await session.execute(
                        select(Rate.id).where(Rate.code == code, Rate.effective_date == effective_date).limit(1)
                    )
                    if existing_rate.scalar_one_or_none() is None:
                        session.add(Rate(code=code, rate_mid=rate_mid, effective_date=effective_date, source="NBP"))
                        inserted += 1
                rows += inserted
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
    return rows


async def import_gold(session, client: NBPClient, start: dt.date, end: dt.date) -> int:
    rows = 0
    for chunk_start, chunk_end in daterange_chunks(start, end, 90):
        data = await client.fetch_gold(chunk_start, chunk_end)
        for item in data:
            effective_date = dt.datetime.strptime(item["data"], "%Y-%m-%d").date()
            price = item["cena"]
            inserted = 0
            if session.bind.dialect.name == "postgresql":
                stmt_gold = (
                    pg_insert(GoldPrice)
                    .values(price=price, effective_date=effective_date, source="NBP")
                    .on_conflict_do_nothing(index_elements=[GoldPrice.effective_date])
                )
                res_gold = await session.execute(stmt_gold)
                inserted += res_gold.rowcount or 0
            else:
                existing_gold = await session.execute(
                    select(GoldPrice.id).where(GoldPrice.effective_date == effective_date).limit(1)
                )
                if existing_gold.scalar_one_or_none() is None:
                    session.add(GoldPrice(price=price, effective_date=effective_date, source="NBP"))
                    inserted += 1
            rows += inserted
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
    return rows


async def run_full_history(session, client: NBPClient) -> None:
    today = dt.date.today()
    start = dt.date(2002, 1, 2)
    logger.info("Import full history from %s to %s", start, today)
    rows_rates = await import_rates(session, client, start, today)
    rows_gold = await import_gold(session, client, start, today)
    await publish(settings.redis_pubsub_channel_rates, {
        "type": "full",
        "asset": "ALL",
        "from": str(start),
        "to": str(today),
        "rows": rows_rates + rows_gold,
        "job_id": None,
    })
    logger.info("Full history imported: rates=%s gold=%s", rows_rates, rows_gold)


async def run_incremental(session, client: NBPClient) -> None:
    today = dt.date.today()
    yesterday = today - dt.timedelta(days=1)
    # For currencies NBP publishes only business days; fetch last 3 days to be safe
    start = today - dt.timedelta(days=3)
    rows_rates = await import_rates(session, client, start, today)
    rows_gold = await import_gold(session, client, start, today)
    await publish(settings.redis_pubsub_channel_rates, {
        "type": "incremental",
        "asset": "ALL",
        "from": str(start),
        "to": str(today),
        "rows": rows_rates + rows_gold,
        "job_id": None,
    })
    logger.info("Incremental imported rates=%s gold=%s", rows_rates, rows_gold)


async def run_job(job_type: str):
    start_ts = utc_now_naive()
    async with session_scope() as session:
        job = JobLog(job_type=job_type, status=JobStatus.success, started_at=start_ts)
        session.add(job)
        await session.flush()
        client = NBPClient()
        try:
            if job_type == "bootstrap":
                rows_before = job.rows_written or 0
                await run_full_history(session, client)
                job.rows_written = rows_before  # placeholder; detailed counts already published
            else:
                rows_rates = await import_rates(session, client, dt.date.today() - dt.timedelta(days=3), dt.date.today())
                rows_gold = await import_gold(session, client, dt.date.today() - dt.timedelta(days=3), dt.date.today())
                await publish(settings.redis_pubsub_channel_rates, {
                    "type": "incremental",
                    "asset": "ALL",
                    "from": str(dt.date.today() - dt.timedelta(days=3)),
                    "to": str(dt.date.today()),
                    "rows": rows_rates + rows_gold,
                    "job_id": job.id,
                })
                job.rows_written = rows_rates + rows_gold
            job.status = JobStatus.success
        except Exception as exc:  # pragma: no cover - runtime safety
            logger.exception("Job %s failed", job_type)
            job.status = JobStatus.failed
            job.error = str(exc)
        finally:
            job.finished_at = utc_now_naive()
            await session.commit()
            await client.close()


async def main():
    await ensure_schema()
    scheduler = AsyncIOScheduler()
    # Zawsze uruchom jednorazowy bootstrap (bezpieczny dzięki ON CONFLICT DO NOTHING).
    scheduler.add_job(run_job, trigger="date", args=["bootstrap"], run_date=utc_now_naive())
    scheduler.add_job(
        run_job,
        "interval",
        seconds=settings.refresh_seconds,
        args=["incremental"],
        next_run_time=utc_now_naive(),
    )
    scheduler.start()
    logger.info("Miner started, refresh %ss", settings.refresh_seconds)
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
