import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    global _redis_client
    if not settings.redis_enabled:
        return None
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis unavailable: %s", exc)
            _redis_client = None
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    client = get_redis()
    if not client:
        return None
    try:
        data = await client.get(key)
        if data is None:
            return None
        return json.loads(data)
    except Exception as exc:  # pragma: no cover
        logger.warning("Redis get failed: %s", exc)
        return None


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    client = get_redis()
    if not client:
        return
    try:
        await client.set(key, json.dumps(value, default=str), ex=ttl or settings.redis_cache_ttl)
    except Exception as exc:  # pragma: no cover
        logger.warning("Redis set failed: %s", exc)


async def cache_delete_pattern(pattern: str) -> None:
    client = get_redis()
    if not client:
        return
    try:
        async for key in client.scan_iter(match=pattern):
            await client.delete(key)
    except Exception as exc:  # pragma: no cover
        logger.warning("Redis delete pattern failed: %s", exc)


async def publish(channel: str, message: dict) -> None:
    client = get_redis()
    if not client:
        return
    try:
        await client.publish(channel, json.dumps(message))
    except Exception as exc:  # pragma: no cover
        logger.warning("Redis publish failed: %s", exc)

