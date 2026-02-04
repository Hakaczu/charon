import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .db import Base


class JobStatus(str, enum.Enum):
    success = "success"
    failed = "failed"
    skipped = "skipped"


class SignalType(str, enum.Enum):
    buy = "BUY"
    hold = "HOLD"
    sell = "SELL"


class Currency(Base):
    __tablename__ = "currencies"

    code = Column(String(8), primary_key=True)
    name = Column(String(128), nullable=False)
    source = Column(String(32), nullable=False, default="NBP")

    rates = relationship("Rate", back_populates="currency", cascade="all, delete-orphan")


class Rate(Base):
    __tablename__ = "rates"
    __table_args__ = (UniqueConstraint("code", "effective_date", name="uq_rate_code_date"),)

    id = Column(Integer, primary_key=True)
    code = Column(String(8), ForeignKey("currencies.code"), nullable=False)
    rate_mid = Column(Numeric(18, 6), nullable=False)
    effective_date = Column(Date, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(32), nullable=False, default="NBP")

    currency = relationship("Currency", back_populates="rates")


class GoldPrice(Base):
    __tablename__ = "gold_prices"
    __table_args__ = (UniqueConstraint("effective_date", name="uq_gold_date"),)

    id = Column(Integer, primary_key=True)
    price = Column(Numeric(18, 6), nullable=False)
    effective_date = Column(Date, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(32), nullable=False, default="NBP")


class JobLog(Base):
    __tablename__ = "jobs_log"

    id = Column(Integer, primary_key=True)
    job_type = Column(String(32), nullable=False)
    status = Column(Enum(JobStatus), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    rows_written = Column(Integer, default=0)
    error = Column(String(512))


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True)
    asset_code = Column(String(16), nullable=False)
    signal = Column(Enum(SignalType), nullable=False)
    macd = Column(Numeric(18, 6), nullable=False)
    signal_line = Column(Numeric(18, 6), nullable=False)
    histogram = Column(Numeric(18, 6), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    horizon_days = Column(Integer, default=0)


class AnalysisSnapshot(Base):
    __tablename__ = "analysis_snapshots"

    id = Column(Integer, primary_key=True)
    asset_code = Column(String(16), nullable=False)
    window_name = Column(String(32), nullable=False)
    stats = Column(String, nullable=False)  # JSON string for simplicity
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
