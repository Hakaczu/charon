from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Instrument, JobRun, Rate, Signal
from app.services.nbp_client import NbpClient
from app.services.scheduler import next_run
from app.services.signal_engine import MODEL_VERSION, calculate_signal

logger = logging.getLogger(__name__)

CURRENCY_CODES = ["USD", "EUR", "CHF", "GBP", "NOK", "JPY", "SEK", "CAD", "AUD"]
GOLD_CODE = "XAU"
SILVER_CODE = "XAG"


class FetchError(Exception):
    pass


def _retry_fetch(fetcher, retries: int = 3, backoff: float = 1.5):
    for attempt in range(retries):
        try:
            return fetcher()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404 and attempt < retries - 1:
                time.sleep(backoff**attempt)
                continue
            raise


def _fetch_table_with_fallback(client: NbpClient, table: str):
    try:
        return _retry_fetch(lambda: client._get(f"/api/exchangerates/tables/{table}?format=json"))
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise
    return client._get(f"/api/exchangerates/tables/{table}/last/1?format=json")


def _fetch_gold_with_fallback(client: NbpClient):
    try:
        return _retry_fetch(lambda: client.fetch_gold())
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise
    return client._get("/api/cenyzlota/last/1?format=json")


def _ensure_instruments(db: Session):
    existing = {inst.code for inst in db.scalars(select(Instrument))}
    defaults = [
        ("USD", "currency", "US Dollar"),
        ("EUR", "currency", "Euro"),
        ("CHF", "currency", "Swiss Franc"),
        ("GBP", "currency", "British Pound"),
        ("NOK", "currency", "Norwegian Krone"),
        ("JPY", "currency", "Japanese Yen"),
        ("SEK", "currency", "Swedish Krona"),
        ("CAD", "currency", "Canadian Dollar"),
        ("AUD", "currency", "Australian Dollar"),
        (GOLD_CODE, "metal", "Gold"),
        (SILVER_CODE, "metal", "Silver"),
    ]
    for code, type_, name in defaults:
        if code in existing:
            continue
        enabled = code != SILVER_CODE
        db.add(Instrument(code=code, type=type_, name=name, enabled=enabled))
    db.commit()


def _get_rates_by_code(table_payload: list[dict]) -> dict[str, dict]:
    rates = table_payload[0]["rates"]
    return {rate["code"]: rate for rate in rates}


def _upsert_rate(db: Session, instrument: Instrument, source: str, effective_date, mid=None, bid=None, ask=None, price_pln_per_g=None):
    exists = db.scalar(
        select(Rate).where(
            Rate.instrument_id == instrument.id,
            Rate.source == source,
            Rate.effective_date == effective_date,
        )
    )
    if exists:
        return
    db.add(
        Rate(
            instrument_id=instrument.id,
            source=source,
            effective_date=effective_date,
            mid=mid,
            bid=bid,
            ask=ask,
            price_pln_per_g=price_pln_per_g,
        )
    )


def _calculate_and_store_signal(db: Session, instrument: Instrument, effective_date, bid=None, ask=None):
    mids = [row.mid for row in db.scalars(
        select(Rate).where(
            Rate.instrument_id == instrument.id,
            Rate.source == "A",
        ).order_by(Rate.effective_date)
    )]
    result = calculate_signal(mids, bid, ask)
    exists = db.scalar(
        select(Signal).where(
            Signal.instrument_id == instrument.id,
            Signal.as_of_date == effective_date,
            Signal.model_version == MODEL_VERSION,
        )
    )
    if exists:
        return
    db.add(
        Signal(
            instrument_id=instrument.id,
            as_of_date=effective_date,
            signal=result.signal,
            confidence=result.confidence,
            score=result.score,
            explain_json=result.explain | {"summary": result.summary},
            model_version=MODEL_VERSION,
        )
    )


def run_fetch_job(db: Session):
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    job_run = JobRun(
        job_name="daily_fetch",
        started_at=datetime.now(tz=timezone.utc),
        status="running",
    )
    db.add(job_run)
    db.commit()
    try:
        _ensure_instruments(db)
        client = NbpClient()
        table_a = _fetch_table_with_fallback(client, "A")
        table_c = _fetch_table_with_fallback(client, "C")
        gold = _fetch_gold_with_fallback(client)

        effective_date = table_a[0]["effectiveDate"]
        effective_date = datetime.fromisoformat(effective_date).date()
        rates_a = _get_rates_by_code(table_a)
        rates_c = _get_rates_by_code(table_c)

        instruments = {inst.code: inst for inst in db.scalars(select(Instrument))}
        for code in CURRENCY_CODES:
            inst = instruments[code]
            mid = rates_a[code]["mid"]
            bid = rates_c[code]["bid"]
            ask = rates_c[code]["ask"]
            _upsert_rate(db, inst, "A", effective_date, mid=mid)
            _upsert_rate(db, inst, "C", effective_date, bid=bid, ask=ask)
            _calculate_and_store_signal(db, inst, effective_date, bid=bid, ask=ask)

        gold_entry = gold[0]
        gold_date = datetime.fromisoformat(gold_entry["data"]).date()
        gold_price = gold_entry["cena"]
        gold_inst = instruments[GOLD_CODE]
        _upsert_rate(db, gold_inst, "GOLD", gold_date, price_pln_per_g=gold_price)

        db.commit()
        job_run.status = "success"
        job_run.last_effective_date = effective_date
    except Exception as exc:
        logger.exception("Fetch job failed")
        db.rollback()
        job_run.status = "failed"
        job_run.error_message = str(exc)
    finally:
        job_run.finished_at = datetime.now(tz=timezone.utc)
        job_run.next_run_at = next_run(settings.schedule_cron, settings.timezone, datetime.now(tz=tz))
        db.commit()

    return job_run
