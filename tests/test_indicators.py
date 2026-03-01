import pytest
import pandas as pd
import numpy as np
from services.indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_sma,
    calculate_ema,
    calculate_atr,
    calculate_stochastic,
    add_all_indicators,
    get_signal_summary,
)


@pytest.fixture
def sample_price_series():
    np.random.seed(42)
    n = 100
    prices = 100 + np.cumsum(np.random.randn(n) * 2)
    return pd.Series(prices, name="Close")


@pytest.fixture
def sample_ohlcv():
    np.random.seed(42)
    n = 100
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    open_ = close + np.random.randn(n) * 0.5
    volume = np.random.randint(100000, 1000000, n).astype(float)
    df = pd.DataFrame({
        "Open": open_,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
    })
    return df


def test_rsi_returns_series(sample_price_series):
    rsi = calculate_rsi(sample_price_series)
    assert isinstance(rsi, pd.Series)
    assert len(rsi) == len(sample_price_series)


def test_rsi_values_in_range(sample_price_series):
    rsi = calculate_rsi(sample_price_series)
    valid = rsi.dropna()
    assert (valid >= 0).all()
    assert (valid <= 100).all()


def test_macd_returns_three_series(sample_price_series):
    macd, signal, hist = calculate_macd(sample_price_series)
    assert isinstance(macd, pd.Series)
    assert isinstance(signal, pd.Series)
    assert isinstance(hist, pd.Series)
    assert len(macd) == len(sample_price_series)


def test_macd_histogram_equals_difference(sample_price_series):
    macd, signal, hist = calculate_macd(sample_price_series)
    diff = (macd - signal).dropna()
    hist_clean = hist.dropna()
    common_idx = diff.index.intersection(hist_clean.index)
    pd.testing.assert_series_equal(
        diff.loc[common_idx].round(10),
        hist_clean.loc[common_idx].round(10),
    )


def test_bollinger_bands_ordering(sample_price_series):
    upper, mid, lower = calculate_bollinger_bands(sample_price_series)
    valid_idx = upper.dropna().index
    assert (upper.loc[valid_idx] >= mid.loc[valid_idx]).all()
    assert (mid.loc[valid_idx] >= lower.loc[valid_idx]).all()


def test_sma_correct_length(sample_price_series):
    sma = calculate_sma(sample_price_series, period=20)
    assert len(sma) == len(sample_price_series)
    assert sma.iloc[:19].isna().all()
    assert not pd.isna(sma.iloc[19])


def test_ema_correct_length(sample_price_series):
    ema = calculate_ema(sample_price_series, period=9)
    assert len(ema) == len(sample_price_series)


def test_atr_non_negative(sample_ohlcv):
    atr = calculate_atr(sample_ohlcv["High"], sample_ohlcv["Low"], sample_ohlcv["Close"])
    valid = atr.dropna()
    assert (valid >= 0).all()


def test_stochastic_values_in_range(sample_ohlcv):
    k, d = calculate_stochastic(sample_ohlcv["High"], sample_ohlcv["Low"], sample_ohlcv["Close"])
    valid_k = k.dropna()
    valid_d = d.dropna()
    assert (valid_k >= 0).all()
    assert (valid_k <= 100).all()
    assert (valid_d >= 0).all()
    assert (valid_d <= 100).all()


def test_add_all_indicators_returns_dataframe(sample_ohlcv):
    result = add_all_indicators(sample_ohlcv)
    assert isinstance(result, pd.DataFrame)
    expected_cols = ["rsi", "macd", "macd_signal", "bb_upper", "bb_lower", "sma_20", "atr"]
    for col in expected_cols:
        assert col in result.columns, f"Missing column: {col}"


def test_add_all_indicators_does_not_modify_original(sample_ohlcv):
    original_cols = list(sample_ohlcv.columns)
    add_all_indicators(sample_ohlcv)
    assert list(sample_ohlcv.columns) == original_cols


def test_signal_summary_returns_dict(sample_ohlcv):
    df_with_ind = add_all_indicators(sample_ohlcv)
    signals = get_signal_summary(df_with_ind)
    assert isinstance(signals, dict)


def test_rsi_period_14_by_default(sample_price_series):
    rsi = calculate_rsi(sample_price_series)
    assert pd.isna(rsi.iloc[0])
