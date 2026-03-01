from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    direction = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    entry_date = Column(DateTime, default=datetime.utcnow)
    exit_date = Column(DateTime, nullable=True)
    pnl = Column(Float, default=0.0)
    pnl_pct = Column(Float, default=0.0)
    exit_reason = Column(String, nullable=True)
    strategy = Column(String, nullable=True)
    status = Column(String, default="open")
    take_profit = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_equity = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    parameters = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    alert_price_above = Column(Float, nullable=True)
    alert_price_below = Column(Float, nullable=True)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    equity = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    positions_value = Column(Float, nullable=False)
    daily_pnl = Column(Float, default=0.0)
    cumulative_pnl = Column(Float, default=0.0)
