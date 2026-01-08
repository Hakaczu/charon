from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.jobs.fetch_rates import run_fetch_job
from app.models import Instrument, JobRun, Rate, Signal
from app.schemas import (
    InstrumentResponse,
    QuoteHistoryPoint,
    QuoteResponse,
    SignalResponse,
    StatusResponse,
)
from app.services.scheduler import next_run

router = APIRouter()


@router.get("/status", response_model=StatusResponse)

def status(db: Session = Depends(get_db)):
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    last_run = db.scalar(select(JobRun).order_by(JobRun.started_at.desc()))
    next_run_at = last_run.next_run_at if last_run and last_run.next_run_at else next_run(settings.schedule_cron, settings.timezone)
    return StatusResponse(
        last_run=last_run.finished_at.astimezone(tz) if last_run and last_run.finished_at else None,
        last_effective_date=last_run.last_effective_date if last_run else None,
        next_run_at=next_run_at.astimezone(tz) if next_run_at else None,
        service_time=datetime.now(tz=tz),
        version=settings.service_version,
    )


@router.get("/instruments", response_model=list[InstrumentResponse])

def instruments(db: Session = Depends(get_db)):
    results = db.scalars(select(Instrument).order_by(Instrument.code)).all()
    return [InstrumentResponse(code=item.code, name=item.name, type=item.type, enabled=item.enabled) for item in results]


@router.get("/quotes/latest", response_model=list[QuoteResponse])

def latest_quotes(codes: str = Query(""), db: Session = Depends(get_db)):
    code_list = [code.strip().upper() for code in codes.split(",") if code.strip()]
    query = select(Instrument).where(Instrument.code.in_(code_list)) if code_list else select(Instrument)
    instruments = db.scalars(query).all()
    responses = []
    for inst in instruments:
        if inst.type == "metal":
            latest_metal = db.scalar(
                select(Rate)
                .where(Rate.instrument_id == inst.id, Rate.source == "GOLD")
                .order_by(Rate.effective_date.desc())
            )
            if not latest_metal:
                continue
            responses.append(
                QuoteResponse(
                    code=inst.code,
                    effective_date=latest_metal.effective_date,
                    mid=latest_metal.price_pln_per_g,
                    bid=None,
                    ask=None,
                )
            )
            continue
        latest_mid = db.scalar(
            select(Rate)
            .where(Rate.instrument_id == inst.id, Rate.source == "A")
            .order_by(Rate.effective_date.desc())
        )
        latest_bid_ask = db.scalar(
            select(Rate)
            .where(Rate.instrument_id == inst.id, Rate.source == "C")
            .order_by(Rate.effective_date.desc())
        )
        latest = latest_mid or latest_bid_ask
        if not latest:
            continue
        responses.append(
            QuoteResponse(
                code=inst.code,
                effective_date=latest.effective_date,
                mid=latest_mid.mid if latest_mid else None,
                bid=latest_bid_ask.bid if latest_bid_ask else None,
                ask=latest_bid_ask.ask if latest_bid_ask else None,
            )
        )
    return responses


@router.get("/quotes/{code}/history", response_model=list[QuoteHistoryPoint])

def quote_history(code: str, days: int = Query(90, ge=1, le=365), db: Session = Depends(get_db)):
    inst = db.scalar(select(Instrument).where(Instrument.code == code.upper()))
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")
    source = "A" if inst.type == "currency" else "GOLD"
    results = db.scalars(
        select(Rate)
        .where(Rate.instrument_id == inst.id, Rate.source == source)
        .order_by(Rate.effective_date.desc())
        .limit(days)
    ).all()
    return [
        QuoteHistoryPoint(
            effective_date=row.effective_date,
            mid=row.mid if inst.type == "currency" else row.price_pln_per_g,
            bid=row.bid,
            ask=row.ask,
        )
        for row in reversed(results)
    ]


@router.get("/signals/latest", response_model=list[SignalResponse])

def latest_signals(codes: str = Query(""), db: Session = Depends(get_db)):
    code_list = [code.strip().upper() for code in codes.split(",") if code.strip()]
    query = select(Instrument).where(Instrument.code.in_(code_list)) if code_list else select(Instrument)
    instruments = db.scalars(query).all()
    responses = []
    for inst in instruments:
        latest_signal = db.scalar(
            select(Signal)
            .where(Signal.instrument_id == inst.id)
            .order_by(Signal.as_of_date.desc())
        )
        if not latest_signal:
            continue
        summary = latest_signal.explain_json.get("summary", "")
        responses.append(
            SignalResponse(
                code=inst.code,
                as_of_date=latest_signal.as_of_date,
                signal=latest_signal.signal,
                confidence=float(latest_signal.confidence),
                score=float(latest_signal.score),
                explain_summary=summary,
                explain_json=latest_signal.explain_json,
            )
        )
    return responses


@router.post("/admin/run-fetch")

def admin_run_fetch(
    x_admin_token: str = Header(""),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    job = run_fetch_job(db)
    return {
        "status": job.status,
        "last_effective_date": job.last_effective_date,
        "finished_at": job.finished_at,
    }
