import pytest
import pandas as pd
import numpy as np
from services.risk import (
    calculate_position_size,
    calculate_var,
    calculate_cvar,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_profit_factor,
    calculate_expectancy,
)


@pytest.fixture
def sample_returns():
    np.random.seed(42)
    returns = pd.Series(np.random.randn(252) * 0.01 + 0.0003)
    return returns


@pytest.fixture
def sample_equity():
    np.random.seed(42)
    returns = np.random.randn(252) * 0.01 + 0.0003
    equity = pd.Series(100000 * (1 + returns).cumprod())
    return equity


@pytest.fixture
def winning_trades():
    return [
        {"pnl": 500},
        {"pnl": 300},
        {"pnl": -200},
        {"pnl": 150},
        {"pnl": -100},
    ]


def test_position_size_basic():
    size = calculate_position_size(100000, 100, 0.02, 0.05)
    assert isinstance(size, int)
    assert size > 0


def test_position_size_zero_price():
    size = calculate_position_size(100000, 0, 0.02, 0.05)
    assert size == 0


def test_position_size_zero_stop_loss():
    size = calculate_position_size(100000, 100, 0.02, 0.0)
    assert size == 0


def test_var_returns_float(sample_returns):
    var = calculate_var(sample_returns)
    assert isinstance(var, float)
    assert var < 0


def test_var_confidence_levels(sample_returns):
    var_95 = calculate_var(sample_returns, 0.95)
    var_99 = calculate_var(sample_returns, 0.99)
    assert var_99 <= var_95


def test_cvar_worse_than_var(sample_returns):
    var = calculate_var(sample_returns, 0.95)
    cvar = calculate_cvar(sample_returns, 0.95)
    assert cvar <= var


def test_sharpe_ratio_returns_float(sample_returns):
    sharpe = calculate_sharpe_ratio(sample_returns)
    assert isinstance(sharpe, float)


def test_sharpe_ratio_empty_series():
    sharpe = calculate_sharpe_ratio(pd.Series(dtype=float))
    assert sharpe == 0.0


def test_sortino_ratio_returns_float(sample_returns):
    sortino = calculate_sortino_ratio(sample_returns)
    assert isinstance(sortino, float)


def test_max_drawdown_negative_or_zero(sample_equity):
    mdd = calculate_max_drawdown(sample_equity)
    assert mdd <= 0


def test_max_drawdown_monotonically_increasing():
    equity = pd.Series([100, 110, 120, 130, 140])
    mdd = calculate_max_drawdown(equity)
    assert mdd == 0.0


def test_max_drawdown_empty():
    mdd = calculate_max_drawdown(pd.Series(dtype=float))
    assert mdd == 0.0


def test_win_rate_calculation(winning_trades):
    wr = calculate_win_rate(winning_trades)
    assert wr == pytest.approx(0.6)


def test_win_rate_empty():
    assert calculate_win_rate([]) == 0.0


def test_profit_factor_positive(winning_trades):
    pf = calculate_profit_factor(winning_trades)
    assert isinstance(pf, float)
    assert pf > 0


def test_profit_factor_no_losses():
    trades = [{"pnl": 100}, {"pnl": 200}]
    pf = calculate_profit_factor(trades)
    assert pf == float("inf")


def test_expectancy_returns_float(winning_trades):
    exp = calculate_expectancy(winning_trades)
    assert isinstance(exp, float)


def test_expectancy_empty():
    assert calculate_expectancy([]) == 0.0
