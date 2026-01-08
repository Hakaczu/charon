from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    last_run: datetime | None
    last_effective_date: date | None
    next_run_at: datetime | None
    service_time: datetime
    version: str


class InstrumentResponse(BaseModel):
    code: str
    name: str
    type: str
    enabled: bool


class QuoteResponse(BaseModel):
    code: str
    effective_date: date
    mid: float | None
    bid: float | None
    ask: float | None


class QuoteHistoryPoint(BaseModel):
    effective_date: date
    mid: float | None
    bid: float | None
    ask: float | None


class SignalResponse(BaseModel):
    code: str
    as_of_date: date
    signal: str
    confidence: float
    score: float
    explain_summary: str
    explain_json: dict[str, Any]
    disclaimer: str = Field(default="Informational only, not financial advice.")
