"""Charon – prosta aplikacja do pobierania kursów NBP i decyzji buy/sell/hold."""

import logging
import os
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional, Tuple, TypedDict
from apscheduler.schedulers.background import BackgroundScheduler

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from charon import db
from charon.decision import DecisionResult, decide_from_history
from charon.constants import TOP10_CURRENCIES, CURRENCY_ICON_CLASS
from charon import collector
from charon import cache as cache_utils
from charon.nbp_client import (
    NBPError,
    fetch_table,
    get_recent_currency_history,
    get_recent_gold_history,
)

LOG_FILE = os.getenv("LOG_FILE", "charon.log")


def _configure_logging() -> None:
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    rotating = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
    rotating.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[stream, rotating])


_configure_logging()

app = Flask(__name__)

# Wczytaj .env jeśli istnieje
load_dotenv()

# Konfiguracja
DECISION_BIAS_PERCENT = 1.0  # próg procentowy względem średniej
HISTORY_DAYS = 60
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "3600"))
PORT = int(os.getenv("PORT", "5000"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "1") == "1"
REDIS_CACHE_KEY = os.getenv("REDIS_CACHE_KEY", "charon:cache")

# constants imported from charon.constants

class CacheStore(TypedDict):
    items: List[DecisionResult]
    last_fetch: Optional[datetime]
    history_map: Dict[str, List[Tuple[str, float]]]


# Cache danych, aby nie pobierać z NBP przy każdym odświeżeniu strony
_CACHE: CacheStore = {
    "items": [],
    "last_fetch": None,
    "history_map": {},
}
# Lazy Redis client
_redis_client: Optional[Any] = None


def _get_redis() -> Optional[Any]:
    global _redis_client
    if _redis_client is None:
        _redis_client = cache_utils.get_redis_client()
    return _redis_client

# Scheduler instance (if started)
_SCHEDULER: Optional[BackgroundScheduler] = None

# Inicjalizacja bazy przy starcie aplikacji
db.init_db()


def _decorate_decision(decision: DecisionResult, code: str, name: str) -> DecisionResult:
    decision.code = code
    decision.name = name
    decision.icon_class = CURRENCY_ICON_CLASS.get(code.upper(), "fa-solid fa-coins")
    return decision


def _build_instruments() -> Tuple[List[DecisionResult], datetime, Dict[str, List[Tuple[str, float]]]]:
    """Delegate collection to `charon.collector.collect` and return results."""
    decisions, fetched_at, history_map = collector.collect(codes=TOP10_CURRENCIES, days=HISTORY_DAYS)
    # Ensure `name` and `code` are set for UI (collector sets icon_class)
    table = fetch_table("A")
    table_map = {item["code"]: item for item in table}
    for d in decisions:
        if not d.name:
            d.name = table_map.get(d.code, {}).get("currency", d.code)
    return decisions, fetched_at, history_map


def _ensure_cached_data() -> Tuple[List[DecisionResult], Optional[datetime], Optional[datetime], Dict[str, List[Tuple[str, float]]]]:
    # Serve from in-memory cache if available
    last_fetch: Optional[datetime] = _CACHE.get("last_fetch")
    if last_fetch:
        next_refresh = last_fetch + timedelta(seconds=REFRESH_SECONDS)
        return _CACHE.get("items", []), last_fetch, next_refresh, _CACHE.get("history_map", {})

    # Try to hydrate from Redis if in-memory is empty
    client = _get_redis()
    if client:
        try:
            raw = client.get(REDIS_CACHE_KEY)
            if raw:
                items, last_fetch, history_map = cache_utils.deserialize_snapshot(raw)
                _CACHE["items"] = items
                _CACHE["last_fetch"] = last_fetch
                _CACHE["history_map"] = history_map
                next_refresh = last_fetch + timedelta(seconds=REFRESH_SECONDS) if last_fetch else None
                return items, last_fetch, next_refresh, history_map
        except Exception:
            logging.exception("Failed to load cache from redis")

    # If still empty, return whatever is there (likely empty) without fetching NBP
    return _CACHE.get("items", []), _CACHE.get("last_fetch"), None, _CACHE.get("history_map", {})


def refresh_data() -> None:
    """Force a fresh fetch from NBP and update DB + cache."""
    logging.info("Refreshing data from NBP...")
    try:
        instruments, fetched_at, history_map = _build_instruments()
        _CACHE["items"] = instruments
        _CACHE["last_fetch"] = fetched_at
        _CACHE["history_map"] = history_map
        # Persist to Redis for cross-process cache
        client = _get_redis()
        if client:
            try:
                client.setex(
                    REDIS_CACHE_KEY,
                    REFRESH_SECONDS * 3,
                    cache_utils.serialize_snapshot(instruments, fetched_at, history_map),
                )
            except Exception:
                logging.exception("Failed to write cache to redis")
        logging.info("Refreshed %d instruments at %s", len(instruments), fetched_at.isoformat())
    except Exception:
        logging.exception("Error during refresh_data")


def start_scheduler(interval_seconds: Optional[int] = None, run_immediately: bool = False) -> BackgroundScheduler:
    """Start background scheduler to refresh data periodically.

    Returns the scheduler instance.
    """
    global _SCHEDULER
    if _SCHEDULER is not None:
        logging.info("Scheduler already running")
        return _SCHEDULER

    sched = BackgroundScheduler()
    seconds = interval_seconds or REFRESH_SECONDS
    next_run = datetime.now(timezone.utc) if run_immediately else None
    sched.add_job(refresh_data, "interval", seconds=seconds, next_run_time=next_run)
    sched.start()
    _SCHEDULER = sched
    logging.info("Scheduler started with interval %s seconds", seconds)
    return sched


def stop_scheduler() -> None:
    """Stop background scheduler if running."""
    global _SCHEDULER
    if _SCHEDULER is None:
        return
    logging.info("Shutting down scheduler")
    try:
        _SCHEDULER.shutdown(wait=False)
    finally:
        _SCHEDULER = None


def _fmt_ts(ts: Optional[datetime]) -> str:
    if not ts:
        return "—"
    return ts.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def _series_to_points(series: List[Tuple[str, float]]):
    return [{"date": d, "value": float(v)} for d, v in series]


def _compute_metrics(series: List[Tuple[str, float]]):
    values = [float(v) for _, v in series]
    if not values:
        return {"avg": None, "min": None, "max": None, "std": None, "last": None, "last_date": None}
    n = len(values)
    avg = sum(values) / n
    min_v = min(values)
    max_v = max(values)
    last_v = values[-1]
    last_date = series[-1][0]
    # proste odchylenie standardowe populacyjne
    variance = sum((v - avg) ** 2 for v in values) / n
    std = variance ** 0.5
    return {"avg": avg, "min": min_v, "max": max_v, "std": std, "last": last_v, "last_date": last_date}


@app.route("/")
def index():
    try:
        instruments, last_fetch, next_refresh, history_map = _ensure_cached_data()
        chart_data = {code: _series_to_points(series) for code, series in history_map.items()}
        analytics = {code: _compute_metrics(series) for code, series in history_map.items()}
        items_js = [{"code": d.code, "name": d.name} for d in instruments]
        return render_template(
            "index.html",
            items=instruments,
            last_fetch=_fmt_ts(last_fetch),
            next_refresh=_fmt_ts(next_refresh),
            refresh_seconds=REFRESH_SECONDS,
            chart_data=chart_data,
            analytics=analytics,
            items_js=items_js,
        )
    except Exception as exc:  # pragma: no cover - UI fallback
        logging.exception("Błąd podczas budowy widoku")
        return f"Wystąpił błąd: {exc}", 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.errorhandler(NBPError)
def handle_nbp_error(error: NBPError):
    return jsonify({"error": str(error)}), 502


if __name__ == "__main__":
    if os.getenv("SCHEDULER_ENABLED", "1") == "1":
        # start scheduler and do an immediate refresh
        start_scheduler(run_immediately=True)
    try:
        app.run(debug=True, host="0.0.0.0", port=PORT)
    finally:
        stop_scheduler()