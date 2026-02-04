from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_session, Base, engine
from .models import Rate, GoldPrice, Signal, JobLog
from .schemas import RateOut, GoldOut, SignalOut, JobLogOut, MinerStats, SourcesList, SourceInfo
from .cache import cache_get, cache_set

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title="Charon API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/sources", response_model=SourcesList)
async def sources():
    return SourcesList(sources=[SourceInfo(name="NBP", base_url=settings.nbp_base_url)])


@app.get("/rates", response_model=List[RateOut])
async def get_rates(code: str, from_date: Optional[date] = None, to_date: Optional[date] = None, session: AsyncSession = Depends(get_session)):
    cache_key = f"cache:rates:{code}:{from_date}:{to_date}"
    cached = await cache_get(cache_key)
    if cached:
        return cached
    query = select(Rate).where(Rate.code == code)
    if from_date:
        query = query.where(Rate.effective_date >= from_date)
    if to_date:
        query = query.where(Rate.effective_date <= to_date)
    query = query.order_by(Rate.effective_date)
    res = await session.execute(query)
    items = res.scalars().all()
    result = [RateOut.from_orm(item) for item in items]
    await cache_set(cache_key, [r.dict() for r in result])
    return result


@app.get("/gold", response_model=List[GoldOut])
async def get_gold(from_date: Optional[date] = None, to_date: Optional[date] = None, session: AsyncSession = Depends(get_session)):
    cache_key = f"cache:gold:{from_date}:{to_date}"
    cached = await cache_get(cache_key)
    if cached:
        return cached
    query = select(GoldPrice)
    if from_date:
        query = query.where(GoldPrice.effective_date >= from_date)
    if to_date:
        query = query.where(GoldPrice.effective_date <= to_date)
    query = query.order_by(GoldPrice.effective_date)
    res = await session.execute(query)
    items = res.scalars().all()
    result = [GoldOut.from_orm(item) for item in items]
    await cache_set(cache_key, [r.dict() for r in result])
    return result


@app.get("/signals", response_model=List[SignalOut])
async def get_signals(code: str, limit: int = 100, session: AsyncSession = Depends(get_session)):
    cache_key = f"cache:signals:{code}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return cached
    query = select(Signal).where(Signal.asset_code == code).order_by(Signal.generated_at.desc()).limit(limit)
    res = await session.execute(query)
    items = res.scalars().all()
    result = [SignalOut.from_orm(item) for item in items]
    await cache_set(cache_key, [r.dict() for r in result])
    return result


@app.get("/stats/miner", response_model=MinerStats)
async def miner_stats(session: AsyncSession = Depends(get_session)):
    total = await session.scalar(select(func.count()).select_from(JobLog))
    res = await session.execute(select(JobLog).order_by(JobLog.started_at.desc()).limit(20))
    jobs = res.scalars().all()
    success_jobs = len([j for j in jobs if j.status.name == "success"])
    failed_jobs = len([j for j in jobs if j.status.name == "failed"])
    return MinerStats(total_jobs=total or len(jobs), success_jobs=success_jobs, failed_jobs=failed_jobs, last_jobs=[JobLogOut.from_orm(j) for j in jobs])
