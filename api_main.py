import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from charon import cache as cache_utils
from charon.decision import DecisionResult

load_dotenv()

REDIS_CACHE_KEY = os.getenv("REDIS_CACHE_KEY", "charon:cache")

app = FastAPI(title="Charon API", version="1.0.0")


def _get_snapshot() -> Dict[str, Any]:
    client = cache_utils.get_redis_client()
    if not client:
        return {"items": [], "history_map": {}, "last_fetch": None}
    raw = client.get(REDIS_CACHE_KEY)
    if not raw:
        return {"items": [], "history_map": {}, "last_fetch": None}
    items, last_fetch, history_map = cache_utils.deserialize_snapshot(raw)
    return {
        "items": [item.__dict__ for item in items],
        "history_map": history_map,
        "last_fetch": last_fetch.isoformat() if isinstance(last_fetch, datetime) else None,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/snapshot")
async def snapshot():
    return _get_snapshot()


@app.get("/api/v1/rates")
async def rates():
    snap = _get_snapshot()
    return snap.get("items", [])


@app.get("/api/v1/history")
async def history(code: str):
    snap = _get_snapshot()
    history_map: Dict[str, List[Tuple[str, float]]] = snap.get("history_map", {})
    if code not in history_map:
        raise HTTPException(status_code=404, detail="Code not found")
    return {"code": code, "points": history_map[code]}
