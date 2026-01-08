from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))

    rates: Mapped[list[Rate]] = relationship("Rate", back_populates="instrument")
    signals: Mapped[list[Signal]] = relationship("Signal", back_populates="instrument")


class Rate(Base):
    __tablename__ = "rates"
    __table_args__ = (UniqueConstraint("instrument_id", "source", "effective_date", name="uq_rate_instrument_source_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), index=True)
    source: Mapped[str] = mapped_column(String(20))
    effective_date: Mapped[date] = mapped_column(Date)
    mid: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    bid: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    ask: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    price_pln_per_g: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))

    instrument: Mapped[Instrument] = relationship("Instrument", back_populates="rates")


class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (UniqueConstraint("instrument_id", "as_of_date", "model_version", name="uq_signal_instrument_date_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), index=True)
    as_of_date: Mapped[date] = mapped_column(Date)
    signal: Mapped[str] = mapped_column(String(10))
    confidence: Mapped[float] = mapped_column(Numeric(6, 4))
    score: Mapped[float] = mapped_column(Numeric(10, 6))
    explain_json: Mapped[dict] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))

    instrument: Mapped[Instrument] = relationship("Instrument", back_populates="signals")


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_name: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    last_effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
