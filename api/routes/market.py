from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from services.market_data import (
    get_quote,
    get_multiple_quotes,
    fetch_ohlcv,
    fetch_ohlcv_range,
    get_news_headlines,
    get_full_news,
    get_market_movers,
    get_correlation_matrix,
)
from services.indicators import add_all_indicators, get_signal_summary
from services.sentiment import get_aggregate_sentiment
from models.schemas import QuoteResponse, SentimentResponse, IndicatorResponse

router = APIRouter()


@router.get("/quote/{symbol}", response_model=QuoteResponse)
async def get_stock_quote(symbol: str):
    try:
        return get_quote(symbol.upper())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quotes")
async def get_multiple_stock_quotes(symbols: str = Query(..., description="Comma-separated symbols")):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    try:
        return get_multiple_quotes(symbol_list)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{symbol}")
async def get_price_history(
    symbol: str,
    period: str = Query(default="1y", description="1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max"),
    interval: str = Query(default="1d", description="1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo"),
):
    try:
        df = fetch_ohlcv(symbol.upper(), period=period, interval=interval)
        if df is None or len(df) == 0:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        data = df.reset_index()
        return {
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "data": [
                {
                    "date": str(row["Date"] if "Date" in data.columns else row["Datetime"]),
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(float(row["Close"]), 4),
                    "volume": int(row["Volume"]),
                }
                for _, row in data.iterrows()
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/indicators/{symbol}")
async def get_technical_indicators(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
):
    try:
        df = fetch_ohlcv(symbol.upper(), period=period, interval=interval)
        if df is None or len(df) < 50:
            raise HTTPException(status_code=422, detail="Insufficient data for indicators")
        df_with_indicators = add_all_indicators(df)
        signals = get_signal_summary(df_with_indicators)

        latest = df_with_indicators.iloc[-1]
        return {
            "symbol": symbol.upper(),
            "last_updated": str(df_with_indicators.index[-1]),
            "close": round(float(latest["Close"]), 4),
            "rsi": round(float(latest.get("rsi", 0) or 0), 2),
            "macd": round(float(latest.get("macd", 0) or 0), 4),
            "macd_signal": round(float(latest.get("macd_signal", 0) or 0), 4),
            "macd_hist": round(float(latest.get("macd_hist", 0) or 0), 4),
            "bb_upper": round(float(latest.get("bb_upper", 0) or 0), 4),
            "bb_mid": round(float(latest.get("bb_mid", 0) or 0), 4),
            "bb_lower": round(float(latest.get("bb_lower", 0) or 0), 4),
            "sma_20": round(float(latest.get("sma_20", 0) or 0), 4),
            "sma_50": round(float(latest.get("sma_50", 0) or 0), 4),
            "sma_200": round(float(latest.get("sma_200", 0) or 0), 4),
            "atr": round(float(latest.get("atr", 0) or 0), 4),
            "stoch_k": round(float(latest.get("stoch_k", 0) or 0), 2),
            "stoch_d": round(float(latest.get("stoch_d", 0) or 0), 2),
            "signals": signals,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/news/{symbol}")
async def get_stock_news(symbol: str, limit: int = Query(default=10, le=50)):
    try:
        news = get_full_news(symbol.upper())
        return {
            "symbol": symbol.upper(),
            "count": min(len(news), limit),
            "news": news[:limit],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sentiment/{symbol}")
async def get_stock_sentiment(symbol: str):
    try:
        headlines = get_news_headlines(symbol.upper())
        if not headlines:
            return {
                "symbol": symbol.upper(),
                "sentiment": "neutral",
                "probability": 0.0,
                "news_count": 0,
                "headlines": [],
            }
        result = get_aggregate_sentiment(headlines)
        return {
            "symbol": symbol.upper(),
            "sentiment": result["sentiment"],
            "probability": round(result["probability"], 4),
            "news_count": len(headlines),
            "headlines": headlines[:10],
            "breakdown": result["breakdown"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/movers")
async def get_top_movers():
    try:
        return get_market_movers()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/correlation")
async def get_symbol_correlation(
    symbols: str = Query(..., description="Comma-separated symbols"),
    period: str = Query(default="1y"),
):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    try:
        corr = get_correlation_matrix(symbol_list, period=period)
        return {
            "symbols": symbol_list,
            "correlation": corr.round(4).to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
