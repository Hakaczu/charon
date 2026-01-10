import logging
import os
import time
from typing import List

from dotenv import load_dotenv

from charon import cache as cache_utils
from charon import collector

load_dotenv()

REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "3600"))
REDIS_CACHE_KEY = os.getenv("REDIS_CACHE_KEY", "charon:cache")

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("charon.miner")


def run_once():
  logger.info("Miner: starting collection")
  decisions, fetched_at, history_map = collector.collect()
  client = cache_utils.get_redis_client()
  if client:
    try:
      client.setex(
        REDIS_CACHE_KEY,
        REFRESH_SECONDS * 3,
        cache_utils.serialize_snapshot(decisions, fetched_at, history_map),
      )
      logger.info("Miner: stored snapshot to redis at %s", fetched_at.isoformat())
    except Exception:
      logger.exception("Miner: failed to store snapshot to redis")
  else:
    logger.warning("Miner: redis client not available, skipping snapshot store")


def main():
  while True:
    try:
      run_once()
    except Exception:
      logger.exception("Miner: run_once failed")
    time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
  main()
