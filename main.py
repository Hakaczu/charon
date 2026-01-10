"""Charon – prosta aplikacja do pobierania kursów NBP i decyzji buy/sell/hold."""

import logging
import os
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from typing import List, Optional, Tuple, TypedDict
from apscheduler.schedulers.background import BackgroundScheduler

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from charon import db
from charon.decision import DecisionResult, decide_from_history
from charon.constants import TOP10_CURRENCIES, CURRENCY_ICON_CLASS
from charon import collector
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

# constants imported from charon.constants

class CacheStore(TypedDict):
    items: List[DecisionResult]
    last_fetch: Optional[datetime]


# Cache danych, aby nie pobierać z NBP przy każdym odświeżeniu strony
_CACHE: CacheStore = {
    "items": [],
    "last_fetch": None,
}

# Scheduler instance (if started)
_SCHEDULER: Optional[BackgroundScheduler] = None

# Inicjalizacja bazy przy starcie aplikacji
db.init_db()


def _decorate_decision(decision: DecisionResult, code: str, name: str) -> DecisionResult:
    decision.code = code
    decision.name = name
    decision.icon_class = CURRENCY_ICON_CLASS.get(code.upper(), "fa-solid fa-coins")
    return decision


def _build_instruments() -> Tuple[List[DecisionResult], datetime]:
    """Delegate collection to `charon.collector.collect` and return results."""
    decisions, fetched_at = collector.collect(codes=TOP10_CURRENCIES, days=HISTORY_DAYS)
    # Ensure `name` and `code` are set for UI (collector sets icon_class)
    table = fetch_table("A")
    table_map = {item["code"]: item for item in table}
    for d in decisions:
        if not d.name:
            d.name = table_map.get(d.code, {}).get("currency", d.code)
    return decisions, fetched_at


def _ensure_cached_data() -> Tuple[List[DecisionResult], Optional[datetime], Optional[datetime]]:
    now = datetime.now(timezone.utc)
    last_fetch: Optional[datetime] = _CACHE["last_fetch"]
    needs_refresh = last_fetch is None or (now - last_fetch) >= timedelta(seconds=REFRESH_SECONDS)

    if needs_refresh:
        instruments, fetched_at = _build_instruments()
        _CACHE["items"] = instruments
        _CACHE["last_fetch"] = fetched_at
        last_fetch = fetched_at

    next_refresh = last_fetch + timedelta(seconds=REFRESH_SECONDS) if last_fetch else None
    return _CACHE.get("items", []), last_fetch, next_refresh


def refresh_data() -> None:
    """Force a fresh fetch from NBP and update DB + cache."""
    logging.info("Refreshing data from NBP...")
    try:
        instruments, fetched_at = _build_instruments()
        _CACHE["items"] = instruments
        _CACHE["last_fetch"] = fetched_at
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


@app.route("/")
def index():
    try:
        instruments, last_fetch, next_refresh = _ensure_cached_data()
        return render_template(
            "index.html",
            items=instruments,
            last_fetch=_fmt_ts(last_fetch),
            next_refresh=_fmt_ts(next_refresh),
            refresh_seconds=REFRESH_SECONDS,
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