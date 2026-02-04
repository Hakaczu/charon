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
from src.shared.backtester import Backtester
import pandas as pd
import os
import sys

sys.path.append('/app')

from src.shared.database import get_db, init_db
from src.shared.models import Rate, GoldPrice, Signal, JobLog, Currency

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_client = redis.from_url(REDIS_URL, encoding="utf8") # Removed decode_responses=True
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

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

@app.get("/stats/miner")
async def get_miner_stats(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    query = select(JobLog).order_by(desc(JobLog.started_at)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/stats/upcoming")
async def get_upcoming_jobs():
    """
    Calculates the next scheduled run times based on the fixed cron schedule in Europe/Warsaw.
    Rates: Every hour at minute 0.
    Gold: Every hour at minute 2.
    """
    tz = ZoneInfo("Europe/Warsaw")
    now = datetime.now(tz)
    
    # Calculate next Rates job (Minute 0)
    next_rates = now.replace(minute=0, second=0, microsecond=0)
    if next_rates <= now:
        next_rates += timedelta(hours=1)
        
    # Calculate next Gold job (Minute 2)
    next_gold = now.replace(minute=2, second=0, microsecond=0)
    if next_gold <= now:
        next_gold += timedelta(hours=1)
        
    return {
        "import_rates": next_rates,
        "import_gold": next_gold,
        "server_time": now
    }

@app.post("/backtest")
async def run_backtest(
    asset_code: str = Query(..., description="Currency code (e.g. USD) or 'GOLD'"),
    initial_capital: float = 10000.0,
    db: AsyncSession = Depends(get_db)
):
    """
    Runs a backtest simulation for the specified asset using the current strategy.
    """
    # 1. Fetch History
    if asset_code.upper() == "GOLD":
        stmt = select(GoldPrice).order_by(GoldPrice.effective_date.asc())
        result = await db.execute(stmt)
        data = result.scalars().all()
        # Normalize
        df = pd.DataFrame([{'date': d.effective_date, 'price': float(d.price)} for d in data])
    else:
        stmt = select(Rate).where(Rate.currency_code == asset_code.upper()).order_by(Rate.effective_date.asc())
        result = await db.execute(stmt)
        data = result.scalars().all()
        df = pd.DataFrame([{'date': d.effective_date, 'price': float(d.rate_mid)} for d in data])
        
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {asset_code}")
        
    # 2. Run Backtest
    backtester = Backtester(initial_capital=initial_capital)
    results = backtester.run(df)
    
    return results

@app.get("/stats/correlation")
@cache(expire=3600)
async def get_correlation_matrix(db: AsyncSession = Depends(get_db)):
    """
    Calculates correlation matrix between Gold and Top 7 currencies for the last 180 days.
    """
    assets = ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD"]
    merged_df = pd.DataFrame()

    for asset in assets:
        if asset == "GOLD":
            stmt = select(GoldPrice).order_by(GoldPrice.effective_date.desc()).limit(180)
            result = await db.execute(stmt)
            data = result.scalars().all()
            df = pd.DataFrame([{'date': d.effective_date, asset: float(d.price)} for d in data])
        else:
            stmt = select(Rate).where(Rate.currency_code == asset).order_by(Rate.effective_date.desc()).limit(180)
            result = await db.execute(stmt)
            data = result.scalars().all()
            df = pd.DataFrame([{'date': d.effective_date, asset: float(d.rate_mid)} for d in data])
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            if merged_df.empty:
                merged_df = df
            else:
                merged_df = pd.merge(merged_df, df, on='date', how='inner')

    if merged_df.empty:
        return {}

    # Drop date for correlation calc
    corr_matrix = merged_df.drop(columns=['date']).corr()
    
    # Format for JSON response (dict of dicts)
    return corr_matrix.to_dict()

@app.get("/predict")
@cache(expire=3600)
async def predict_future(
    asset_code: str = Query(..., description="Currency code (e.g. USD) or 'GOLD'"),
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    Predicts future prices for the next X days using Facebook Prophet.
    """
    from prophet import Prophet
    
    # 1. Fetch History (last 2 years for better seasonality)
    if asset_code.upper() == "GOLD":
        stmt = select(GoldPrice).order_by(GoldPrice.effective_date.asc())
        result = await db.execute(stmt)
        data = result.scalars().all()
        df = pd.DataFrame([{'ds': d.effective_date, 'y': float(d.price)} for d in data])
    else:
        stmt = select(Rate).where(Rate.currency_code == asset_code.upper()).order_by(Rate.effective_date.asc())
        result = await db.execute(stmt)
        data = result.scalars().all()
        df = pd.DataFrame([{'ds': d.effective_date, 'y': float(d.rate_mid)} for d in data])

    if len(df) < 30:
        raise HTTPException(status_code=400, detail="Not enough data for prediction")

    # Prophet expects 'ds' to be datetime naive
    df['ds'] = pd.to_datetime(df['ds']).dt.tz_localize(None)

    # 2. Train Model
    m = Prophet(daily_seasonality=False) # NBP is daily anyway
    m.fit(df)

    # 3. Forecast
    future = m.make_future_dataframe(periods=days)
    forecast = m.predict(future)

    # Return only the future part
    predictions = forecast.iloc[-days:][['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    
    return predictions.to_dict(orient='records')

@app.get("/stats/seasonality")
@cache(expire=3600)
async def get_seasonality(
    asset_code: str = Query(..., description="Currency code or 'GOLD'"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculates monthly returns heat map data.
    """
    # 1. Fetch Full History
    if asset_code.upper() == "GOLD":
        stmt = select(GoldPrice).order_by(GoldPrice.effective_date.asc())
        result = await db.execute(stmt)
        data = result.scalars().all()
        df = pd.DataFrame([{'date': d.effective_date, 'price': float(d.price)} for d in data])
    else:
        stmt = select(Rate).where(Rate.currency_code == asset_code.upper()).order_by(Rate.effective_date.asc())
        result = await db.execute(stmt)
        data = result.scalars().all()
        df = pd.DataFrame([{'date': d.effective_date, 'price': float(d.rate_mid)} for d in data])
        
    if df.empty:
        raise HTTPException(status_code=404, detail="No data")

    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    # Resample to monthly closing price to calculate monthly return
    # Group by Year-Month, take the LAST price of the month
    monthly_df = df.sort_values('date').groupby(['year', 'month']).last().reset_index()
    
    # Calculate Percentage Change
    monthly_df['pct_change'] = monthly_df['price'].pct_change() * 100
    
    # Pivot for Heatmap: Index=Year, Columns=Month, Values=PctChange
    pivot_df = monthly_df.pivot(index='year', columns='month', values='pct_change')
    
    # Fill NaN (first month usually) with 0
    pivot_df = pivot_df.fillna(0)
    
    # Return structure suitable for frontend reconstruction
    # reset_index to keep year as column
    return pivot_df.reset_index().to_dict(orient='records')
