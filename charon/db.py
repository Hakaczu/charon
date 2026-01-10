"""Warstwa dostępu do bazy dla Charon (SQLAlchemy)."""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from typing import Iterable, List, Tuple

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker

RatePoint = Tuple[str, float]

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///charon.db")
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
Base = declarative_base()


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    url = Column(String(250), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Currency(Base):
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True)
    code = Column(String(3), nullable=False, unique=True)
    name = Column(String(250), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Rate(Base):
    __tablename__ = "rates"

    id = Column(Integer, primary_key=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    effective_date = Column(Date, nullable=False)
    mid_rate = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("currency_id", "effective_date", name="uniq_currency_date"),)


class GoldPrice(Base):
    __tablename__ = "gold_prices"

    id = Column(Integer, primary_key=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    effective_date = Column(Date, nullable=False, unique=True)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# --- API ---


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()


def _get_or_create_datasource(session, name: str, url: str) -> DataSource:
    ds = session.query(DataSource).filter_by(name=name, url=url).first()
    if ds:
        return ds
    ds = DataSource(name=name, url=url)
    session.add(ds)
    session.commit()
    session.refresh(ds)
    return ds


def _get_or_create_currency(session, code: str, name: str) -> Currency:
    cur = session.query(Currency).filter_by(code=code).first()
    if cur:
        if cur.name != name:
            cur.name = name
            session.commit()
        return cur
    cur = Currency(code=code, name=name)
    session.add(cur)
    session.commit()
    session.refresh(cur)
    return cur


def _parse_date(date_str: str) -> date:
    return datetime.fromisoformat(date_str).date()


def save_currency_history(
    session,
    code: str,
    name: str,
    history: Iterable[RatePoint],
    source_name: str = "NBP API",
    source_url: str = "https://api.nbp.pl/api",
) -> int:
    """Zapisuje historię kursów waluty; zwraca liczbę dodanych rekordów (bez duplikatów)."""
    datasource = _get_or_create_datasource(session, source_name, source_url)
    currency = _get_or_create_currency(session, code, name)

    existing_dates = {
        row[0]
        for row in session.query(Rate.effective_date)
        .filter(Rate.currency_id == currency.id)
        .all()
    }

    inserted = 0
    for date_str, mid in history:
        eff_date = _parse_date(date_str)
        if eff_date in existing_dates:
            continue
        session.add(
            Rate(
                currency_id=currency.id,
                data_source_id=datasource.id,
                effective_date=eff_date,
                mid_rate=float(mid),
            )
        )
        inserted += 1
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise
    return inserted


def save_gold_history(
    session,
    history: Iterable[RatePoint],
    source_name: str = "NBP API",
    source_url: str = "https://api.nbp.pl/api",
) -> int:
    datasource = _get_or_create_datasource(session, source_name, source_url)
    existing_dates = {row[0] for row in session.query(GoldPrice.effective_date).all()}

    inserted = 0
    for date_str, price in history:
        eff_date = _parse_date(date_str)
        if eff_date in existing_dates:
            continue
        session.add(
            GoldPrice(
                data_source_id=datasource.id,
                effective_date=eff_date,
                price=float(price),
            )
        )
        inserted += 1
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise
    return inserted


def latest_rates(session, limit: int = 10) -> List[Rate]:
    return (
        session.query(Rate)
        .order_by(Rate.effective_date.desc())
        .limit(limit)
        .all()
    )


def latest_gold(session, limit: int = 10) -> List[GoldPrice]:
    return (
        session.query(GoldPrice)
        .order_by(GoldPrice.effective_date.desc())
        .limit(limit)
        .all()
    )
