import asyncio
import logging
import os
import sys
from datetime import date, datetime, timedelta
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
import json

# Fix import path for shared modules in Docker
sys.path.append('/app')

from src.shared.database import init_db, AsyncSessionLocal
from src.shared.models import Currency, Rate, GoldPrice, JobLog, JobStatus
from src.miner.nbp_client import NBPClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("miner")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "1") == "1"

class MinerService:
    def __init__(self):
        self.nbp_client = NBPClient()
        self.redis = redis.from_url(REDIS_URL) if REDIS_ENABLED else None

    async def get_last_rate_date(self, session: AsyncSession) -> date:
        result = await session.execute(select(func.max(Rate.effective_date)))
        last_date = result.scalar()
        return last_date if last_date else date(2023, 1, 1) # Default start history

    async def get_last_gold_date(self, session: AsyncSession) -> date:
        result = await session.execute(select(func.max(GoldPrice.effective_date)))
        last_date = result.scalar()
        return last_date if last_date else date(2023, 1, 1)

    async def publish_event(self, channel: str, payload: dict):
        if self.redis:
            try:
                await self.redis.publish(channel, json.dumps(payload))
                logger.info(f"Published event to {channel}: {payload}")
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")

    async def run_import_rates(self):
        logger.info("Starting Rates Import Job")
        async with AsyncSessionLocal() as session:
            job = JobLog(job_type="import_rates", status=JobStatus.PENDING)
            session.add(job)
            await session.commit()
            
            try:
                last_date = await self.get_last_rate_date(session)
                today = date.today()
                
                if last_date >= today:
                    logger.info("Rates are up to date.")
                    job.status = JobStatus.SKIPPED
                    job.finished_at = datetime.now()
                    await session.commit()
                    return

                # Fetch from next day
                start_date = last_date + timedelta(days=1)
                rates_data = await self.nbp_client.fetch_exchange_rates(start_date, today)
                
                rows_count = 0
                if rates_data:
                    # Ensure currencies exist
                    unique_currencies = {r['code']: r['currency'] for r in rates_data}
                    
                    # Simple check and insert currencies (could be optimized)
                    for code, name in unique_currencies.items():
                        curr_res = await session.execute(select(Currency).where(Currency.code == code))
                        if not curr_res.scalar():
                            session.add(Currency(code=code, name=name))
                    
                    await session.commit() # Commit currencies first

                    for r in rates_data:
                        # Check specific existence to avoid constraint errors on re-runs (or use ON CONFLICT DO NOTHING in raw SQL)
                        # Here we rely on the loop logic mostly, but let's be safe
                        stmt = select(Rate).where(Rate.currency_code == r['code'], Rate.effective_date == date.fromisoformat(r['effectiveDate']))
                        exists = await session.execute(stmt)
                        if not exists.scalar():
                            new_rate = Rate(
                                currency_code=r['code'],
                                rate_mid=r['mid'],
                                effective_date=date.fromisoformat(r['effectiveDate'])
                            )
                            session.add(new_rate)
                            rows_count += 1
                    
                    await session.commit()

                job.status = JobStatus.SUCCESS
                job.rows_written = rows_count
                job.finished_at = datetime.now()
                await session.commit()
                logger.info(f"Rates import finished. Rows: {rows_count}")

                if rows_count > 0:
                     await self.publish_event("rates.ingested", {
                         "type": "currency",
                         "from": str(start_date),
                         "to": str(today),
                         "count": rows_count
                     })

            except Exception as e:
                logger.error(f"Job failed: {e}")
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.finished_at = datetime.now()
                await session.commit()

    async def run_import_gold(self):
        logger.info("Starting Gold Import Job")
        async with AsyncSessionLocal() as session:
            job = JobLog(job_type="import_gold", status=JobStatus.PENDING)
            session.add(job)
            await session.commit()
            
            try:
                last_date = await self.get_last_gold_date(session)
                today = date.today()
                
                if last_date >= today:
                    logger.info("Gold prices are up to date.")
                    job.status = JobStatus.SKIPPED
                    job.finished_at = datetime.now()
                    await session.commit()
                    return

                start_date = last_date + timedelta(days=1)
                gold_data = await self.nbp_client.fetch_gold_prices(start_date, today)
                
                rows_count = 0
                if gold_data:
                    for g in gold_data:
                        stmt = select(GoldPrice).where(GoldPrice.effective_date == date.fromisoformat(g['data']))
                        exists = await session.execute(stmt)
                        if not exists.scalar():
                            new_price = GoldPrice(
                                price=g['cena'],
                                effective_date=date.fromisoformat(g['data'])
                            )
                            session.add(new_price)
                            rows_count += 1
                    
                    await session.commit()

                job.status = JobStatus.SUCCESS
                job.rows_written = rows_count
                job.finished_at = datetime.now()
                await session.commit()
                logger.info(f"Gold import finished. Rows: {rows_count}")

                if rows_count > 0:
                     await self.publish_event("rates.ingested", {
                         "type": "gold",
                         "from": str(start_date),
                         "to": str(today),
                         "count": rows_count
                     })

            except Exception as e:
                logger.error(f"Job failed: {e}")
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.finished_at = datetime.now()
                await session.commit()

async def main():
    logger.info("Waiting for database...")
    await asyncio.sleep(5) # Simple wait for DB to be ready in Docker
    await init_db()
    logger.info("Database initialized.")

    service = MinerService()
    
    # Run immediately on startup
    await service.run_import_rates()
    await service.run_import_gold()

    scheduler = AsyncIOScheduler()
    # Schedule every hour
    scheduler.add_job(service.run_import_rates, 'cron', minute=0)
    scheduler.add_job(service.run_import_gold, 'cron', minute=2)
    
    scheduler.start()
    logger.info("Scheduler started. Keeping process alive...")
    
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    asyncio.run(main())
