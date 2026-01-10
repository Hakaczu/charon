import json
import logging
import os
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import redis

from .decision import DecisionResult

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_CACHE_KEY = os.getenv("REDIS_CACHE_KEY", "charon:cache")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "1") == "1"

_logger = logging.getLogger(__name__)


def get_redis_client() -> Optional[redis.Redis]:
    if not REDIS_ENABLED:
        return None
    try:
        return redis.from_url(REDIS_URL, decode_responses=True)
    except Exception:
        _logger.exception("Failed to init redis client")
        return None


def serialize_snapshot(
    instruments: List[DecisionResult],
    fetched_at: datetime,
    history_map: Dict[str, List[Tuple[str, float]]],
) -> str:
    payload = {
        "items": [asdict(item) for item in instruments],
        "history_map": history_map,
        "last_fetch": fetched_at.isoformat(),
    }
    return json.dumps(payload)


def deserialize_snapshot(raw: str) -> Tuple[List[DecisionResult], Optional[datetime], Dict[str, List[Tuple[str, float]]]]:
    data = json.loads(raw)
    items = [DecisionResult(**item) for item in data.get("items", [])]
    last_fetch_str = data.get("last_fetch")
    last_fetch = datetime.fromisoformat(last_fetch_str) if last_fetch_str else None
    history_map = data.get("history_map", {})
    return items, last_fetch, history_map
