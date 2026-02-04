import asyncio
import logging
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
from src.brain.analysis import TechnicalAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("brain")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_CHANNEL = "rates.ingested"

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
            
            # Check the last row for the latest signal
            current_idx = -1
            prev_idx = -2
            
            curr_hist = macd_df.iloc[current_idx]['hist']
            prev_hist = macd_df.iloc[prev_idx]['hist']
            curr_rsi = float(rsi_series.iloc[current_idx])
            
            signal_decision = self.analyzer.determine_signal(curr_hist, prev_hist, curr_rsi)
            
            # Save signal
            new_signal = Signal(
                asset_type=AssetType.CURRENCY,
                asset_code=code,
                signal=SignalType(signal_decision),
                macd=macd_df.iloc[current_idx]['macd'],
                signal_line=macd_df.iloc[current_idx]['signal'],
                histogram=curr_hist,
                rsi=curr_rsi,
                price_at_signal=df.iloc[current_idx]['price'],
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
            
            curr_hist = macd_df.iloc[-1]['hist']
            prev_hist = macd_df.iloc[-2]['hist']
            curr_rsi = float(rsi_series.iloc[-1])
            
            signal_decision = self.analyzer.determine_signal(curr_hist, prev_hist, curr_rsi)
            
            new_signal = Signal(
                asset_type=AssetType.GOLD,
                asset_code="GOLD",
                signal=SignalType(signal_decision),
                macd=macd_df.iloc[-1]['macd'],
                signal_line=macd_df.iloc[-1]['signal'],
                histogram=curr_hist,
                rsi=curr_rsi,
                price_at_signal=df.iloc[-1]['price']
            )
            
            session.add(new_signal)
            await session.commit()
            logger.info(f"Signal generated for GOLD: {signal_decision}")

    async def handle_message(self, message):
        try:
            data = json.loads(message['data'])
            logger.info(f"Received event: {data}")
            
            if data['type'] == 'currency':
                # Re-analyze all active currencies or just modified ones?
                # For simplicity, let's analyze all or extract codes.
                # Since payload doesn't list all codes easily, let's fetch all active currencies.
                async with AsyncSessionLocal() as session:
                    # In a real scenario we'd pass specific codes, but here we scan all.
                    # Or better: check what was updated.
                    # Let's iterate all distinct currencies for now.
                    from src.shared.models import Currency
                    result = await session.execute(select(Currency.code))
                    codes = result.scalars().all()
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
