import asyncio
import logging
import math
import os
import sys
import json
import pandas as pd
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

sys.path.append('/app')

from src.shared.database import init_db, AsyncSessionLocal
from src.shared.models import Rate, GoldPrice, Signal, SignalType, AssetType
from src.shared.analysis import TechnicalAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("brain")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_CHANNEL = "rates.ingested"

def _safe_db(value):
    """Convert NaN/Inf float to None so PostgreSQL stores NULL instead of NaN."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


class BrainService:
    def __init__(self):
        self.analyzer = TechnicalAnalyzer()
        self.redis = redis.from_url(REDIS_URL)

    async def process_currency(self, code: str):
        logger.info(f"Analyzing currency: {code}")
        async with AsyncSessionLocal() as session:
            # Fetch last 100 days to ensure enough data for EMA26
            stmt = select(Rate).where(Rate.currency_code == code).order_by(Rate.effective_date.asc())
            result = await session.execute(stmt)
            rates = result.scalars().all()
            
            if not rates or len(rates) < 26:
                logger.warning(f"Not enough data for {code} to calculate MACD")
                return

            df = pd.DataFrame([{
                'date': r.effective_date,
                'price': float(r.rate_mid)
            } for r in rates])
            
            macd_df = self.analyzer.calculate_macd(df['price'])
            rsi_series = self.analyzer.calculate_rsi(df['price'])
            sma_series = self.analyzer.calculate_sma(df['price'], window=50)
            bb_df = self.analyzer.calculate_bollinger_bands(df['price'])
            adx_series = self.analyzer.calculate_adx(df)
            
            # Weekly Trend
            df_weekly = self.analyzer.resample_to_weekly(df)
            curr_weekly_trend = self.analyzer.get_weekly_trend(df_weekly)
            
            # Check the last row for the latest signal
            current_idx = -1
            prev_idx = -2
            
            curr_hist = macd_df.iloc[current_idx]['hist']
            prev_hist = macd_df.iloc[prev_idx]['hist']
            curr_rsi = float(rsi_series.iloc[current_idx])
            curr_price = float(df.iloc[current_idx]['price'])
            curr_sma = float(sma_series.iloc[current_idx])
            curr_bb_lower = float(bb_df.iloc[current_idx]['bb_lower'])
            curr_bb_upper = float(bb_df.iloc[current_idx]['bb_upper'])
            curr_adx = float(adx_series.iloc[current_idx])
            
            signal_decision = self.analyzer.determine_signal(
                curr_hist, prev_hist, curr_rsi, curr_price, curr_sma, curr_bb_lower, curr_bb_upper, curr_adx, curr_weekly_trend
            )
            
            # Save signal
            new_signal = Signal(
                asset_type=AssetType.CURRENCY,
                asset_code=code,
                signal=SignalType(signal_decision),
                macd=_safe_db(float(macd_df.iloc[current_idx]['macd'])),
                signal_line=_safe_db(float(macd_df.iloc[current_idx]['signal'])),
                histogram=_safe_db(float(curr_hist)),
                rsi=_safe_db(float(curr_rsi)),
                adx=_safe_db(float(curr_adx)),
                weekly_trend=curr_weekly_trend,
                price_at_signal=_safe_db(float(df.iloc[current_idx]['price'])),
                horizon_days=1 
            )
            
            session.add(new_signal)
            await session.commit()
            logger.info(f"Signal generated for {code}: {signal_decision}")

    async def process_gold(self):
        logger.info("Analyzing Gold")
        async with AsyncSessionLocal() as session:
            stmt = select(GoldPrice).order_by(GoldPrice.effective_date.asc())
            result = await session.execute(stmt)
            prices = result.scalars().all()
            
            if not prices or len(prices) < 26:
                return

            df = pd.DataFrame([{
                'date': p.effective_date,
                'price': float(p.price)
            } for p in prices])
            
            macd_df = self.analyzer.calculate_macd(df['price'])
            rsi_series = self.analyzer.calculate_rsi(df['price'])
            sma_series = self.analyzer.calculate_sma(df['price'], window=50)
            bb_df = self.analyzer.calculate_bollinger_bands(df['price'])
            adx_series = self.analyzer.calculate_adx(df)
            
            # Weekly Trend
            df_weekly = self.analyzer.resample_to_weekly(df)
            curr_weekly_trend = self.analyzer.get_weekly_trend(df_weekly)
            
            curr_hist = macd_df.iloc[-1]['hist']
            prev_hist = macd_df.iloc[-2]['hist']
            curr_rsi = float(rsi_series.iloc[-1])
            curr_price = float(df.iloc[-1]['price'])
            curr_sma = float(sma_series.iloc[-1])
            curr_bb_lower = float(bb_df.iloc[-1]['bb_lower'])
            curr_bb_upper = float(bb_df.iloc[-1]['bb_upper'])
            curr_adx = float(adx_series.iloc[-1])
            
            signal_decision = self.analyzer.determine_signal(
                curr_hist, prev_hist, curr_rsi, curr_price, curr_sma, curr_bb_lower, curr_bb_upper, curr_adx, curr_weekly_trend
            )
            
            new_signal = Signal(
                asset_type=AssetType.GOLD,
                asset_code="GOLD",
                signal=SignalType(signal_decision),
                macd=_safe_db(float(macd_df.iloc[-1]['macd'])),
                signal_line=_safe_db(float(macd_df.iloc[-1]['signal'])),
                histogram=_safe_db(float(curr_hist)),
                rsi=_safe_db(float(curr_rsi)),
                adx=_safe_db(float(curr_adx)),
                weekly_trend=curr_weekly_trend,
                price_at_signal=_safe_db(float(df.iloc[-1]['price']))
            )
            
            session.add(new_signal)
            await session.commit()
            logger.info(f"Signal generated for GOLD: {signal_decision}")

    async def handle_message(self, message):
        try:
            data = json.loads(message['data'])
            logger.info(f"Received event: {data}")
            
            if data['type'] == 'currency':
                codes = data.get('codes', [])
                if not codes:
                    logger.warning("Received currency event without codes list; skipping reprocessing.")
                    return
                for code in codes:
                    await self.process_currency(code)
            
            elif data['type'] == 'gold':
                await self.process_gold()
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def run(self):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(REDIS_CHANNEL)
        logger.info(f"Subscribed to {REDIS_CHANNEL}")

        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    await self.handle_message(message)
                
                # Keep alive / watchdog logic could go here
                
            except Exception as e:
                logger.error(f"Listener error: {e}")
                await asyncio.sleep(5)

async def main():
    logger.info("Waiting for database...")
    await asyncio.sleep(5)
    await init_db()
    
    service = BrainService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())
