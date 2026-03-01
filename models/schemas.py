from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TradeBase(BaseModel):
    symbol: str
    direction: str
    quantity: int
    entry_price: float
    strategy: Optional[str] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None


class TradeCreate(TradeBase):
    pass


class TradeResponse(TradeBase):
    id: int
    entry_date: datetime
    exit_price: Optional[float] = None
    exit_date: Optional[datetime] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: Optional[str] = None
    status: str = "open"

    class Config:
        from_attributes = True


class BacktestRequest(BaseModel):
    strategy: str = Field(..., description="Strategy name: ml_sentiment, momentum, mean_reversion")
    symbol: str = Field(default="SPY")
    start_date: str = Field(default="2020-01-01")
    end_date: str = Field(default="2023-12-31")
    initial_capital: float = Field(default=100000.0)
    parameters: Optional[Dict[str, Any]] = Field(default=None)


class BacktestResponse(BaseModel):
    id: int
    strategy: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_equity: Optional[float] = None
    total_return: Optional[float] = None
    total_return_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    trades: Optional[List[Dict]] = None
    equity_curve: Optional[Dict[str, float]] = None
    completed: bool = False


class QuoteResponse(BaseModel):
    symbol: str
    price: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None


class SentimentResponse(BaseModel):
    symbol: str
    sentiment: str
    probability: float
    news_count: int
    headlines: List[str]


class IndicatorResponse(BaseModel):
    symbol: str
    date: str
    close: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_mid: Optional[float] = None
    bb_lower: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    atr: Optional[float] = None


class WatchlistItemCreate(BaseModel):
    symbol: str
    notes: Optional[str] = None
    alert_price_above: Optional[float] = None
    alert_price_below: Optional[float] = None


class WatchlistItemResponse(WatchlistItemCreate):
    id: int
    added_at: datetime

    class Config:
        from_attributes = True


class OrderRequest(BaseModel):
    symbol: str
    qty: int
    side: str = Field(..., description="buy or sell")
    order_type: str = Field(default="market", description="market, limit, stop")
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None


class PortfolioMetrics(BaseModel):
    equity: float
    cash: float
    positions_value: float
    daily_pnl: float
    daily_pnl_pct: float
    total_pnl: float
    total_pnl_pct: float
    positions: List[Dict[str, Any]]
