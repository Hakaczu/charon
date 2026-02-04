from __future__ import annotations

import asyncio
import json
import logging
from typing import List

import redis.asyncio as redis
from sqlalchemy import select, text

from .config import get_settings
from .db import session_scope, engine, Base
from .cache import cache_delete_pattern, get_redis
from .indicators import macd
from .models import Rate, Signal, SignalType, GoldPrice

logger = logging.getLogger(__name__)
settings = get_settings()


async def ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE IF EXISTS rates ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMP DEFAULT now();"))
        await conn.execute(text("ALTER TABLE IF EXISTS rates DROP COLUMN IF EXISTS currency_id;"))


async def compute_for_asset(asset_code: str, prices: List[float]) -> None:
    macd_line, signal_line, histogram = macd(prices)
    if not histogram:
        return
    signal = SignalType.hold
    if histogram[-1] > 0 and (len(histogram) > 1 and histogram[-2] <= 0):
        signal = SignalType.buy
    elif histogram[-1] < 0 and (len(histogram) > 1 and histogram[-2] >= 0):
        signal = SignalType.sell
    async with session_scope() as session:
        s = Signal(
            asset_code=asset_code,
            signal=signal,
            macd=macd_line[-1],
            signal_line=signal_line[-1],
            histogram=histogram[-1],
        )
        session.add(s)
        await session.commit()
    await cache_delete_pattern(f"cache:signals:{asset_code}:*")


async def recompute_all() -> None:
    async with session_scope() as session:
        # currencies
        res = await session.execute(select(Rate.code).distinct())
        codes = [row[0] for row in res.fetchall()]
        for code in codes:
            res_rates = await session.execute(
                select(Rate.rate_mid)
                .where(Rate.code == code)
                .where(Rate.rate_mid.is_not(None))
                .order_by(Rate.effective_date)
            )
            prices = [float(r[0]) for r in res_rates.fetchall() if r[0] is not None]
            await compute_for_asset(code, prices)
        # gold
        res_gold = await session.execute(
            select(GoldPrice.price).where(GoldPrice.price.is_not(None)).order_by(GoldPrice.effective_date)
        )
        prices_gold = [float(r[0]) for r in res_gold.fetchall() if r[0] is not None]
        if prices_gold:
            await compute_for_asset("GOLD", prices_gold)


async def handle_event(message: dict):
    asset = message.get("asset", "ALL")
    # invalidate caches related to incoming asset
    if asset and asset != "ALL":
        await cache_delete_pattern(f"cache:rates:{asset}:*")
        await cache_delete_pattern(f"cache:signals:{asset}:*")
    else:
        await cache_delete_pattern("cache:rates:*")
        await cache_delete_pattern("cache:signals:*")
    await recompute_all()


async def subscriber_loop():
    client = get_redis()
    if not client:
        logger.warning("Redis disabled, running periodic recompute only")
        return
    pubsub = client.pubsub()
    await pubsub.subscribe(settings.redis_pubsub_channel_rates)
    logger.info("Brain listening on %s", settings.redis_pubsub_channel_rates)
    async for msg in pubsub.listen():
        if msg.get("type") != "message":
            continue
        try:
            payload = json.loads(msg["data"])
            await handle_event(payload)
        except Exception as exc:  # pragma: no cover
            logger.warning("Bad message: %s", exc)


async def periodic_loop():
    while True:
        try:
            await recompute_all()
        except Exception:  # pragma: no cover
            logger.exception("Periodic recompute failed")
        await asyncio.sleep(settings.refresh_seconds)


async def main():
    await ensure_schema()
    await recompute_all()  # startowe liczenie sygnałów
    await asyncio.gather(subscriber_loop(), periodic_loop())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
