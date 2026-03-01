from fastapi import APIRouter, HTTPException
from services.portfolio import (
    get_account,
    get_positions,
    get_open_orders,
    is_connected,
)
from services.market_data import fetch_ohlcv
from services.risk import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    compute_rolling_metrics,
)
import pandas as pd

router = APIRouter()


@router.get("/account")
async def get_portfolio_account():
    account = get_account()
    if account is None:
        raise HTTPException(
            status_code=503,
            detail="Alpaca broker not connected. Please configure API credentials.",
        )
    return account


@router.get("/positions")
async def get_portfolio_positions():
    if not is_connected():
        raise HTTPException(
            status_code=503,
            detail="Alpaca broker not connected.",
        )
    return get_positions()


@router.get("/orders")
async def get_open_portfolio_orders():
    if not is_connected():
        raise HTTPException(
            status_code=503,
            detail="Alpaca broker not connected.",
        )
    return get_open_orders()


@router.get("/performance/{symbol}")
async def get_symbol_performance(symbol: str, period: str = "1y"):
    try:
        df = fetch_ohlcv(symbol.upper(), period=period)
        if df is None or len(df) < 2:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")

        returns = df["Close"].pct_change().dropna()
        equity = df["Close"]

        rolling = compute_rolling_metrics(returns)

        return {
            "symbol": symbol.upper(),
            "period": period,
            "total_return": round(float((df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100), 4),
            "sharpe_ratio": round(calculate_sharpe_ratio(returns), 4),
            "max_drawdown": round(calculate_max_drawdown(equity) * 100, 4),
            "annualized_volatility": round(float(returns.std() * (252 ** 0.5) * 100), 4),
            "best_day": round(float(returns.max() * 100), 4),
            "worst_day": round(float(returns.min() * 100), 4),
            "positive_days": int((returns > 0).sum()),
            "negative_days": int((returns < 0).sum()),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def get_connection_status():
    connected = is_connected()
    return {
        "connected": connected,
        "broker": "Alpaca",
        "mode": "paper" if connected else "disconnected",
    }
