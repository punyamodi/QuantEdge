import yfinance as yf
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


def fetch_ohlcv(
    symbol: str, period: str = "1y", interval: str = "1d"
) -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period, interval=interval)
    return data


def fetch_ohlcv_range(
    symbol: str, start: str, end: str, interval: str = "1d"
) -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    data = ticker.history(start=start, end=end, interval=interval)
    return data


def get_current_price(symbol: str) -> float:
    ticker = yf.Ticker(symbol)
    info = ticker.info
    price = (
        info.get("regularMarketPrice")
        or info.get("currentPrice")
        or info.get("previousClose", 0.0)
    )
    return float(price)


def get_ticker_info(symbol: str) -> Dict[str, Any]:
    ticker = yf.Ticker(symbol)
    return ticker.info


def get_quote(symbol: str) -> Dict[str, Any]:
    ticker = yf.Ticker(symbol)
    info = ticker.info
    hist = ticker.history(period="2d")

    price = (
        info.get("regularMarketPrice")
        or info.get("currentPrice")
        or (hist["Close"].iloc[-1] if len(hist) > 0 else 0.0)
    )

    prev_close = info.get("previousClose") or (
        hist["Close"].iloc[-2] if len(hist) > 1 else price
    )
    change = price - prev_close
    change_pct = (change / prev_close * 100) if prev_close != 0 else 0.0

    return {
        "symbol": symbol,
        "price": float(price),
        "open": float(info.get("regularMarketOpen") or info.get("open", price)),
        "high": float(info.get("dayHigh") or info.get("regularMarketDayHigh", price)),
        "low": float(info.get("dayLow") or info.get("regularMarketDayLow", price)),
        "volume": int(info.get("volume") or info.get("regularMarketVolume", 0)),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "week_52_high": info.get("fiftyTwoWeekHigh"),
        "week_52_low": info.get("fiftyTwoWeekLow"),
        "change": float(change),
        "change_pct": float(change_pct),
        "name": info.get("shortName") or info.get("longName", symbol),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "description": info.get("longBusinessSummary"),
        "beta": info.get("beta"),
        "dividend_yield": info.get("dividendYield"),
        "eps": info.get("trailingEps"),
        "forward_pe": info.get("forwardPE"),
    }


def get_multiple_quotes(symbols: List[str]) -> List[Dict[str, Any]]:
    quotes = []
    for symbol in symbols:
        try:
            quotes.append(get_quote(symbol))
        except Exception:
            quotes.append({"symbol": symbol, "price": 0.0, "change_pct": 0.0})
    return quotes


def get_news_headlines(symbol: str) -> List[str]:
    ticker = yf.Ticker(symbol)
    news = ticker.news or []
    headlines = []
    for item in news:
        title = item.get("title") or item.get("headline", "")
        if title:
            headlines.append(title)
    return headlines[:20]


def get_full_news(symbol: str) -> List[Dict[str, Any]]:
    ticker = yf.Ticker(symbol)
    return ticker.news or []


def get_market_movers() -> Dict[str, List[Dict]]:
    indices = ["^GSPC", "^DJI", "^IXIC", "^RUT"]
    index_data = []
    for sym in indices:
        try:
            data = get_quote(sym)
            index_data.append(data)
        except Exception:
            pass

    popular = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META",
        "NVDA", "TSLA", "AMD", "NFLX", "BABA",
    ]
    stock_data = []
    for sym in popular:
        try:
            data = get_quote(sym)
            stock_data.append(data)
        except Exception:
            pass

    stock_data.sort(key=lambda x: abs(x.get("change_pct", 0)), reverse=True)
    gainers = [s for s in stock_data if s.get("change_pct", 0) > 0][:5]
    losers = [s for s in stock_data if s.get("change_pct", 0) < 0][:5]

    return {"indices": index_data, "gainers": gainers, "losers": losers}


def calculate_returns(data: pd.DataFrame) -> pd.Series:
    return data["Close"].pct_change().dropna()


def get_correlation_matrix(symbols: List[str], period: str = "1y") -> pd.DataFrame:
    close_data = {}
    for symbol in symbols:
        try:
            df = fetch_ohlcv(symbol, period=period)
            if len(df) > 0:
                close_data[symbol] = df["Close"]
        except Exception:
            pass
    if not close_data:
        return pd.DataFrame()
    combined = pd.DataFrame(close_data).dropna()
    return combined.corr()
