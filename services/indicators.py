import pandas as pd
import numpy as np
from typing import Tuple, Optional


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def calculate_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: pd.Series, period: int = 20, std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    return prices.rolling(window=period).mean()


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    return prices.ewm(span=period, adjust=False).mean()


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> Tuple[pd.Series, pd.Series]:
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    range_hl = highest_high - lowest_low
    k = 100.0 * (close - lowest_low) / range_hl.replace(0, np.nan)
    d = k.rolling(window=d_period).mean()
    return k, d


def calculate_vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    typical_price = (high + low + close) / 3.0
    cumulative_tp_vol = (typical_price * volume).cumsum()
    cumulative_vol = volume.cumsum()
    return cumulative_tp_vol / cumulative_vol


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum()


def calculate_williams_r(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    range_hl = highest_high - lowest_low
    return -100.0 * (highest_high - close) / range_hl.replace(0, np.nan)


def calculate_cci(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20
) -> pd.Series:
    typical_price = (high + low + close) / 3.0
    sma = typical_price.rolling(window=period).mean()
    mean_deviation = typical_price.rolling(window=period).apply(
        lambda x: np.mean(np.abs(x - np.mean(x))), raw=True
    )
    return (typical_price - sma) / (0.015 * mean_deviation)


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    df["rsi"] = calculate_rsi(close)
    df["macd"], df["macd_signal"], df["macd_hist"] = calculate_macd(close)
    df["bb_upper"], df["bb_mid"], df["bb_lower"] = calculate_bollinger_bands(close)
    df["sma_20"] = calculate_sma(close, 20)
    df["sma_50"] = calculate_sma(close, 50)
    df["sma_200"] = calculate_sma(close, 200)
    df["ema_9"] = calculate_ema(close, 9)
    df["ema_21"] = calculate_ema(close, 21)
    df["atr"] = calculate_atr(high, low, close)
    df["stoch_k"], df["stoch_d"] = calculate_stochastic(high, low, close)
    df["williams_r"] = calculate_williams_r(high, low, close)
    df["cci"] = calculate_cci(high, low, close)

    if "Volume" in df.columns:
        volume = df["Volume"]
        df["vwap"] = calculate_vwap(high, low, close, volume)
        df["obv"] = calculate_obv(close, volume)

    df["returns"] = close.pct_change()
    df["log_returns"] = np.log(close / close.shift(1))
    df["volatility_20"] = df["returns"].rolling(window=20).std() * np.sqrt(252)

    return df


def get_signal_summary(df: pd.DataFrame) -> dict:
    if len(df) < 2:
        return {}

    latest = df.iloc[-1]
    signals = {}

    if not pd.isna(latest.get("rsi")):
        rsi_val = latest["rsi"]
        if rsi_val > 70:
            signals["rsi"] = {"value": round(rsi_val, 2), "signal": "overbought"}
        elif rsi_val < 30:
            signals["rsi"] = {"value": round(rsi_val, 2), "signal": "oversold"}
        else:
            signals["rsi"] = {"value": round(rsi_val, 2), "signal": "neutral"}

    if not pd.isna(latest.get("macd")) and not pd.isna(latest.get("macd_signal")):
        macd_cross = latest["macd"] - latest["macd_signal"]
        prev_cross = df.iloc[-2]["macd"] - df.iloc[-2]["macd_signal"]
        if macd_cross > 0 and prev_cross <= 0:
            signals["macd"] = {"signal": "bullish_crossover"}
        elif macd_cross < 0 and prev_cross >= 0:
            signals["macd"] = {"signal": "bearish_crossover"}
        elif macd_cross > 0:
            signals["macd"] = {"signal": "bullish"}
        else:
            signals["macd"] = {"signal": "bearish"}

    close = latest["Close"]
    if not pd.isna(latest.get("bb_upper")) and not pd.isna(latest.get("bb_lower")):
        if close > latest["bb_upper"]:
            signals["bollinger"] = {"signal": "above_upper_band"}
        elif close < latest["bb_lower"]:
            signals["bollinger"] = {"signal": "below_lower_band"}
        else:
            signals["bollinger"] = {"signal": "within_bands"}

    if not pd.isna(latest.get("sma_50")) and not pd.isna(latest.get("sma_200")):
        if latest["sma_50"] > latest["sma_200"]:
            signals["moving_average"] = {"signal": "golden_cross"}
        else:
            signals["moving_average"] = {"signal": "death_cross"}

    return signals
