from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import date

from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
import redis.asyncio as redis
import os
import sys

sys.path.append('/app')

from src.shared.database import get_db, init_db
from src.shared.models import Rate, GoldPrice, Signal, JobLog, Currency

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_client = redis.from_url(REDIS_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    yield
    # Shutdown

app = FastAPI(title="Charon API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/currencies")
@cache(expire=3600)
async def get_currencies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Currency).where(Currency.active == True))
    return result.scalars().all()

@app.get("/rates")
@cache(expire=60)
async def get_rates(
    code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(Rate).where(Rate.currency_code == code).order_by(desc(Rate.effective_date))
    
    if start_date:
        query = query.where(Rate.effective_date >= start_date)
    if end_date:
        query = query.where(Rate.effective_date <= end_date)
        
    query = query.limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/gold")
@cache(expire=60)
async def get_gold(
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(GoldPrice).order_by(desc(GoldPrice.effective_date)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/signals")
async def get_signals(
    asset_code: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    query = select(Signal).order_by(desc(Signal.generated_at))
    if asset_code:
        query = query.where(Signal.asset_code == asset_code)
    
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/stats/miner")
async def get_miner_stats(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    query = select(JobLog).order_by(desc(JobLog.started_at)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
