import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from services.indicators import add_all_indicators
from services.risk import (
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_profit_factor,
    calculate_calmar_ratio,
    calculate_expectancy,
)
from services.market_data import fetch_ohlcv_range


@dataclass
class BacktestTrade:
    symbol: str
    entry_date: datetime
    entry_price: float
    quantity: int
    direction: str
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""


@dataclass
class BacktestResult:
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_equity: float = 0.0
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    parameters: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        returns = self.equity_curve.pct_change().dropna() if len(self.equity_curve) > 1 else pd.Series()

        trades_list = [
            {
                "entry_date": t.entry_date.isoformat() if t.entry_date else None,
                "exit_date": t.exit_date.isoformat() if t.exit_date else None,
                "entry_price": round(t.entry_price, 4),
                "exit_price": round(t.exit_price, 4) if t.exit_price else None,
                "quantity": t.quantity,
                "direction": t.direction,
                "pnl": round(t.pnl, 2),
                "pnl_pct": round(t.pnl_pct * 100, 4),
                "exit_reason": t.exit_reason,
            }
            for t in self.trades
            if t.exit_date is not None
        ]

        total_return = (self.final_equity - self.initial_capital) / self.initial_capital

        equity_dict = {}
        if len(self.equity_curve) > 0:
            for k, v in self.equity_curve.to_dict().items():
                equity_dict[str(k)] = round(float(v), 2)

        return {
            "strategy": self.strategy_name,
            "symbol": self.symbol,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_capital": self.initial_capital,
            "final_equity": round(self.final_equity, 2),
            "total_return": round(total_return, 6),
            "total_return_pct": round(total_return * 100, 4),
            "sharpe_ratio": round(calculate_sharpe_ratio(returns), 4) if len(returns) > 0 else 0.0,
            "sortino_ratio": round(calculate_sortino_ratio(returns), 4) if len(returns) > 0 else 0.0,
            "max_drawdown": round(calculate_max_drawdown(self.equity_curve), 6) if len(self.equity_curve) > 0 else 0.0,
            "max_drawdown_pct": round(calculate_max_drawdown(self.equity_curve) * 100, 4) if len(self.equity_curve) > 0 else 0.0,
            "calmar_ratio": round(calculate_calmar_ratio(returns, self.equity_curve), 4) if len(returns) > 0 else 0.0,
            "win_rate": round(calculate_win_rate(trades_list), 4),
            "win_rate_pct": round(calculate_win_rate(trades_list) * 100, 2),
            "profit_factor": round(calculate_profit_factor(trades_list), 4),
            "expectancy": round(calculate_expectancy(trades_list), 2),
            "total_trades": len(trades_list),
            "winning_trades": sum(1 for t in trades_list if t["pnl"] > 0),
            "losing_trades": sum(1 for t in trades_list if t["pnl"] < 0),
            "avg_trade_pnl": round(np.mean([t["pnl"] for t in trades_list]), 2) if trades_list else 0.0,
            "trades": trades_list,
            "equity_curve": equity_dict,
        }


class BacktestEngine:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position = None
        self.equity_curve = []
        self.trades: List[BacktestTrade] = []

    def reset(self):
        self.cash = self.initial_capital
        self.position = None
        self.equity_curve = []
        self.trades = []

    def get_equity(self, current_price: float) -> float:
        if self.position is None:
            return self.cash
        position_value = self.position["quantity"] * current_price
        return self.cash + position_value

    def run_momentum_strategy(
        self,
        df: pd.DataFrame,
        symbol: str,
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        cash_at_risk: float = 0.5,
    ) -> BacktestResult:
        self.reset()
        df = add_all_indicators(df.copy())
        df = df.dropna(subset=["rsi", "macd", "macd_signal"])

        equity_values = []
        dates = []

        for i in range(len(df)):
            row = df.iloc[i]
            price = float(row["Close"])
            rsi = float(row["rsi"])
            macd = float(row["macd"])
            macd_signal = float(row["macd_signal"])
            date = df.index[i]

            current_equity = self.get_equity(price)
            equity_values.append(current_equity)
            dates.append(date)

            if self.position:
                tp = self.position.get("take_profit")
                sl = self.position.get("stop_loss")
                if tp and price >= tp:
                    self._close_position(date, price, "take_profit")
                elif sl and price <= sl:
                    self._close_position(date, price, "stop_loss")
                elif (
                    self.position["direction"] == "buy"
                    and rsi > rsi_overbought
                    and macd < macd_signal
                ):
                    self._close_position(date, price, "signal")
            else:
                if rsi < rsi_oversold and macd > macd_signal and self.cash > price:
                    quantity = max(1, int(self.cash * cash_at_risk / price))
                    entry_cost = quantity * price
                    if entry_cost <= self.cash:
                        self.cash -= entry_cost
                        self.position = {
                            "symbol": symbol,
                            "quantity": quantity,
                            "entry_price": price,
                            "entry_date": date,
                            "direction": "buy",
                            "take_profit": price * 1.15,
                            "stop_loss": price * 0.93,
                        }

        if self.position:
            last_price = float(df["Close"].iloc[-1])
            self._close_position(df.index[-1], last_price, "end_of_period")

        equity_series = pd.Series(equity_values, index=dates)
        return BacktestResult(
            strategy_name="Momentum",
            symbol=symbol,
            start_date=df.index[0].to_pydatetime(),
            end_date=df.index[-1].to_pydatetime(),
            initial_capital=self.initial_capital,
            final_equity=equity_values[-1] if equity_values else self.initial_capital,
            trades=self.trades,
            equity_curve=equity_series,
        )

    def run_mean_reversion_strategy(
        self,
        df: pd.DataFrame,
        symbol: str,
        bb_std: float = 2.0,
        cash_at_risk: float = 0.5,
    ) -> BacktestResult:
        self.reset()
        df = add_all_indicators(df.copy())
        df = df.dropna(subset=["bb_upper", "bb_lower", "bb_mid"])

        equity_values = []
        dates = []

        for i in range(len(df)):
            row = df.iloc[i]
            price = float(row["Close"])
            bb_upper = float(row["bb_upper"])
            bb_lower = float(row["bb_lower"])
            bb_mid = float(row["bb_mid"])
            date = df.index[i]

            current_equity = self.get_equity(price)
            equity_values.append(current_equity)
            dates.append(date)

            if self.position:
                if price >= bb_mid or price >= self.position.get("take_profit", float("inf")):
                    self._close_position(date, price, "mean_reversion")
                elif price <= self.position.get("stop_loss", 0):
                    self._close_position(date, price, "stop_loss")
            else:
                if price < bb_lower and self.cash > price:
                    quantity = max(1, int(self.cash * cash_at_risk / price))
                    entry_cost = quantity * price
                    if entry_cost <= self.cash:
                        self.cash -= entry_cost
                        self.position = {
                            "symbol": symbol,
                            "quantity": quantity,
                            "entry_price": price,
                            "entry_date": date,
                            "direction": "buy",
                            "take_profit": bb_mid,
                            "stop_loss": price * 0.95,
                        }

        if self.position:
            last_price = float(df["Close"].iloc[-1])
            self._close_position(df.index[-1], last_price, "end_of_period")

        equity_series = pd.Series(equity_values, index=dates)
        return BacktestResult(
            strategy_name="Mean Reversion",
            symbol=symbol,
            start_date=df.index[0].to_pydatetime(),
            end_date=df.index[-1].to_pydatetime(),
            initial_capital=self.initial_capital,
            final_equity=equity_values[-1] if equity_values else self.initial_capital,
            trades=self.trades,
            equity_curve=equity_series,
        )

    def run_ml_sentiment_strategy(
        self,
        df: pd.DataFrame,
        symbol: str,
        sentiment_data: Dict[str, Any],
        cash_at_risk: float = 0.5,
        sentiment_threshold: float = 0.7,
    ) -> BacktestResult:
        self.reset()
        df = add_all_indicators(df.copy())

        equity_values = []
        dates = []

        for i in range(len(df)):
            row = df.iloc[i]
            price = float(row["Close"])
            date = df.index[i]
            date_str = str(date.date())

            current_equity = self.get_equity(price)
            equity_values.append(current_equity)
            dates.append(date)

            day_sentiment = sentiment_data.get(date_str, {})
            sentiment = day_sentiment.get("sentiment", "neutral")
            probability = day_sentiment.get("probability", 0.0)

            if self.position:
                tp = self.position.get("take_profit")
                sl = self.position.get("stop_loss")
                direction = self.position.get("direction")
                if tp and direction == "buy" and price >= tp:
                    self._close_position(date, price, "take_profit")
                elif sl and direction == "buy" and price <= sl:
                    self._close_position(date, price, "stop_loss")
                elif tp and direction == "sell" and price <= tp:
                    self._close_position(date, price, "take_profit")
                elif sl and direction == "sell" and price >= sl:
                    self._close_position(date, price, "stop_loss")
            else:
                if sentiment == "positive" and probability > sentiment_threshold and self.cash > price:
                    quantity = max(1, int(self.cash * cash_at_risk / price))
                    entry_cost = quantity * price
                    if entry_cost <= self.cash:
                        self.cash -= entry_cost
                        self.position = {
                            "symbol": symbol,
                            "quantity": quantity,
                            "entry_price": price,
                            "entry_date": date,
                            "direction": "buy",
                            "take_profit": price * 1.20,
                            "stop_loss": price * 0.95,
                        }
                elif sentiment == "negative" and probability > sentiment_threshold and self.cash > price:
                    quantity = max(1, int(self.cash * cash_at_risk / price))
                    entry_cost = quantity * price
                    if entry_cost <= self.cash:
                        self.position = {
                            "symbol": symbol,
                            "quantity": quantity,
                            "entry_price": price,
                            "entry_date": date,
                            "direction": "sell",
                            "take_profit": price * 0.80,
                            "stop_loss": price * 1.05,
                        }

        if self.position:
            last_price = float(df["Close"].iloc[-1])
            self._close_position(df.index[-1], last_price, "end_of_period")

        equity_series = pd.Series(equity_values, index=dates)
        return BacktestResult(
            strategy_name="ML Sentiment",
            symbol=symbol,
            start_date=df.index[0].to_pydatetime(),
            end_date=df.index[-1].to_pydatetime(),
            initial_capital=self.initial_capital,
            final_equity=equity_values[-1] if equity_values else self.initial_capital,
            trades=self.trades,
            equity_curve=equity_series,
        )

    def _close_position(self, date: datetime, price: float, reason: str):
        if self.position is None:
            return
        quantity = self.position["quantity"]
        entry_price = self.position["entry_price"]
        direction = self.position["direction"]

        if direction == "buy":
            pnl = (price - entry_price) * quantity
            self.cash += quantity * price
        else:
            pnl = (entry_price - price) * quantity
            self.cash += pnl

        pnl_pct = pnl / (entry_price * quantity) if entry_price != 0 else 0.0

        trade = BacktestTrade(
            symbol=self.position["symbol"],
            entry_date=self.position["entry_date"],
            entry_price=entry_price,
            quantity=quantity,
            direction=direction,
            exit_date=date,
            exit_price=price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=reason,
        )
        self.trades.append(trade)
        self.position = None


def run_backtest(
    strategy: str,
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 100000.0,
    parameters: Optional[Dict] = None,
) -> BacktestResult:
    params = parameters or {}
    df = fetch_ohlcv_range(symbol, start_date, end_date)

    if df is None or len(df) < 50:
        raise ValueError(f"Insufficient data for {symbol} between {start_date} and {end_date}")

    engine = BacktestEngine(initial_capital=initial_capital)

    if strategy == "momentum":
        return engine.run_momentum_strategy(
            df=df,
            symbol=symbol,
            rsi_oversold=params.get("rsi_oversold", 30.0),
            rsi_overbought=params.get("rsi_overbought", 70.0),
            cash_at_risk=params.get("cash_at_risk", 0.5),
        )
    elif strategy == "mean_reversion":
        return engine.run_mean_reversion_strategy(
            df=df,
            symbol=symbol,
            bb_std=params.get("bb_std", 2.0),
            cash_at_risk=params.get("cash_at_risk", 0.5),
        )
    elif strategy == "ml_sentiment":
        return engine.run_ml_sentiment_strategy(
            df=df,
            symbol=symbol,
            sentiment_data=params.get("sentiment_data", {}),
            cash_at_risk=params.get("cash_at_risk", 0.5),
            sentiment_threshold=params.get("sentiment_threshold", 0.7),
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
