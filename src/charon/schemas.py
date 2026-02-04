from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel

from .models import SignalType, JobStatus


class RateOut(BaseModel):
    code: str
    rate_mid: float
    effective_date: date
    source: str

    class Config:
        from_attributes = True


class GoldOut(BaseModel):
    price: float
    effective_date: date
    source: str

    class Config:
        from_attributes = True


class SignalOut(BaseModel):
    asset_code: str
    signal: SignalType
    macd: float
    signal_line: float
    histogram: float
    generated_at: datetime

    class Config:
        from_attributes = True


class JobLogOut(BaseModel):
    job_type: str
    status: JobStatus
    started_at: datetime
    finished_at: Optional[datetime]
    rows_written: int
    error: Optional[str]

    class Config:
        from_attributes = True


class MinerStats(BaseModel):
    total_jobs: int
    success_jobs: int
    failed_jobs: int
    last_jobs: List[JobLogOut]


class SourceInfo(BaseModel):
    name: str
    base_url: str


class SourcesList(BaseModel):
    sources: List[SourceInfo]
