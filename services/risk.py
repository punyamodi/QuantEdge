import pandas as pd
import numpy as np
from typing import List, Optional


def calculate_position_size(
    cash: float,
    price: float,
    risk_pct: float = 0.02,
    stop_loss_pct: float = 0.05,
) -> int:
    if price <= 0 or stop_loss_pct <= 0:
        return 0
    risk_amount = cash * risk_pct
    risk_per_share = price * stop_loss_pct
    return max(0, int(risk_amount / risk_per_share))


def calculate_kelly_fraction(
    win_rate: float, avg_win: float, avg_loss: float
) -> float:
    if avg_loss == 0:
        return 0.0
    b = avg_win / abs(avg_loss)
    p = win_rate
    q = 1 - win_rate
    kelly = (b * p - q) / b
    return max(0.0, min(kelly, 0.25))


def calculate_var(returns: pd.Series, confidence: float = 0.95) -> float:
    clean = returns.dropna()
    if len(clean) == 0:
        return 0.0
    return float(np.percentile(clean, (1 - confidence) * 100))


def calculate_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    var = calculate_var(returns, confidence)
    clean = returns.dropna()
    tail = clean[clean <= var]
    if len(tail) == 0:
        return var
    return float(tail.mean())


def calculate_sharpe_ratio(
    returns: pd.Series, risk_free_rate: float = 0.05, periods: int = 252
) -> float:
    clean = returns.dropna()
    if len(clean) == 0 or clean.std() == 0:
        return 0.0
    excess = clean - risk_free_rate / periods
    return float(excess.mean() / excess.std() * np.sqrt(periods))


def calculate_sortino_ratio(
    returns: pd.Series, risk_free_rate: float = 0.05, periods: int = 252
) -> float:
    clean = returns.dropna()
    if len(clean) == 0:
        return 0.0
    excess = clean - risk_free_rate / periods
    downside = excess[excess < 0]
    if len(downside) == 0 or downside.std() == 0:
        return 0.0
    return float(excess.mean() / downside.std() * np.sqrt(periods))


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    if len(equity_curve) == 0:
        return 0.0
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max
    return float(drawdown.min())


def calculate_calmar_ratio(returns: pd.Series, equity_curve: pd.Series) -> float:
    if len(returns) == 0:
        return 0.0
    annual_return = float((1 + returns.mean()) ** 252 - 1)
    max_dd = abs(calculate_max_drawdown(equity_curve))
    if max_dd == 0:
        return 0.0
    return annual_return / max_dd


def calculate_win_rate(trades: list) -> float:
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
    return wins / len(trades)


def calculate_profit_factor(trades: list) -> float:
    gross_profit = sum(t["pnl"] for t in trades if t.get("pnl", 0) > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t.get("pnl", 0) < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def calculate_expectancy(trades: list) -> float:
    if not trades:
        return 0.0
    win_rate = calculate_win_rate(trades)
    pnls = [t.get("pnl", 0) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    avg_win = np.mean(wins) if wins else 0.0
    avg_loss = np.mean(losses) if losses else 0.0
    return win_rate * avg_win + (1 - win_rate) * avg_loss


def compute_rolling_metrics(returns: pd.Series, window: int = 30) -> pd.DataFrame:
    result = pd.DataFrame(index=returns.index)
    result["rolling_return"] = returns.rolling(window).mean() * 252
    result["rolling_volatility"] = returns.rolling(window).std() * np.sqrt(252)
    rf_daily = 0.05 / 252
    excess = returns - rf_daily
    result["rolling_sharpe"] = (
        excess.rolling(window).mean() / returns.rolling(window).std() * np.sqrt(252)
    )
    return result


def calculate_beta(returns: pd.Series, market_returns: pd.Series) -> float:
    aligned = pd.concat([returns, market_returns], axis=1).dropna()
    if len(aligned) < 2:
        return 1.0
    cov_matrix = aligned.cov()
    market_var = aligned.iloc[:, 1].var()
    if market_var == 0:
        return 1.0
    return float(cov_matrix.iloc[0, 1] / market_var)


def calculate_alpha(
    returns: pd.Series,
    market_returns: pd.Series,
    risk_free_rate: float = 0.05,
) -> float:
    beta = calculate_beta(returns, market_returns)
    ann_return = float((1 + returns.mean()) ** 252 - 1)
    ann_market = float((1 + market_returns.mean()) ** 252 - 1)
    return ann_return - (risk_free_rate + beta * (ann_market - risk_free_rate))
