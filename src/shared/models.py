from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, JSON, ForeignKey, Enum, Index
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum
import datetime

Base = declarative_base()

class AssetType(str, enum.Enum):
    CURRENCY = "currency"
    GOLD = "gold"

class SignalType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class Currency(Base):
    __tablename__ = "currencies"
    
    code = Column(String(3), primary_key=True)
    name = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    
    rates = relationship("Rate", back_populates="currency", cascade="all, delete-orphan")

class Rate(Base):
    __tablename__ = "rates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    currency_code = Column(String(3), ForeignKey("currencies.code"), nullable=False)
    rate_mid = Column(Numeric(10, 4), nullable=False)
    effective_date = Column(Date, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(50), default="NBP")
    
    currency = relationship("Currency", back_populates="rates")
    
    # Ensure unique rate per currency per day
    __table_args__ = (
        Index('idx_rates_code_date', 'currency_code', 'effective_date', unique=True),
    )

class GoldPrice(Base):
    __tablename__ = "gold_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    price = Column(Numeric(10, 4), nullable=False)
    effective_date = Column(Date, nullable=False, unique=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(50), default="NBP")

class JobLog(Base):
    __tablename__ = "jobs_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_type = Column(String(50), nullable=False) # e.g., "import_rates", "import_gold"
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    rows_written = Column(Integer, default=0)
    error_message = Column(String, nullable=True)

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    asset_code = Column(String(10), nullable=False) # 'USD', 'GOLD'
    signal = Column(Enum(SignalType), nullable=False)
    
    # Technical indicators snapshot at time of signal
    macd = Column(Numeric(10, 6), nullable=True)
    signal_line = Column(Numeric(10, 6), nullable=True)
    histogram = Column(Numeric(10, 6), nullable=True)
    rsi = Column(Numeric(10, 4), nullable=True)
    price_at_signal = Column(Numeric(10, 4), nullable=True)
    
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Looking at the last X days of data
    horizon_days = Column(Integer, default=0)

class AnalysisSnapshot(Base):
    __tablename__ = "analysis_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_code = Column(String(10), nullable=False)
    window_days = Column(Integer, default=30)
    stats = Column(JSON, nullable=True) # Store JSON stats like volatility, min, max
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
