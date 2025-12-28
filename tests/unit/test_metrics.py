"""Unit tests for metrics calculations."""
from datetime import datetime

import pandas as pd
import pytest

from lynx.metrics import (
    annualized_return,
    avg_trade_duration,
    calculate_all,
    max_drawdown,
    num_trades,
    profit_factor,
    sharpe_ratio,
    total_return,
    win_rate,
)


@pytest.fixture
def sample_trades():
    """Create sample trades DataFrame for testing."""
    return pd.DataFrame({
        "entry_date": [
            datetime(2024, 1, 1),
            datetime(2024, 2, 1),
            datetime(2024, 3, 1),
            datetime(2024, 4, 1),
            datetime(2024, 5, 1),
        ],
        "exit_date": [
            datetime(2024, 1, 10),
            datetime(2024, 2, 15),
            datetime(2024, 3, 5),
            datetime(2024, 4, 20),
            datetime(2024, 5, 8),
        ],
        "return": [0.05, -0.02, 0.03, -0.01, 0.04],
    })


@pytest.fixture
def winning_trades():
    """Create trades with all winners."""
    return pd.DataFrame({
        "entry_date": [datetime(2024, 1, 1), datetime(2024, 2, 1)],
        "exit_date": [datetime(2024, 1, 10), datetime(2024, 2, 10)],
        "return": [0.10, 0.05],
    })


@pytest.fixture
def losing_trades():
    """Create trades with all losers."""
    return pd.DataFrame({
        "entry_date": [datetime(2024, 1, 1), datetime(2024, 2, 1)],
        "exit_date": [datetime(2024, 1, 10), datetime(2024, 2, 10)],
        "return": [-0.05, -0.03],
    })


@pytest.fixture
def empty_trades():
    """Create empty trades DataFrame."""
    return pd.DataFrame({
        "entry_date": pd.to_datetime([]),
        "exit_date": pd.to_datetime([]),
        "return": [],
    })


def test_total_return(sample_trades):
    """Test total return calculation."""
    result = total_return(sample_trades)
    # (1.05 * 0.98 * 1.03 * 0.99 * 1.04) - 1
    expected = (1.05 * 0.98 * 1.03 * 0.99 * 1.04) - 1
    assert pytest.approx(result, rel=1e-6) == expected


def test_total_return_all_winners(winning_trades):
    """Test total return with all winning trades."""
    result = total_return(winning_trades)
    expected = (1.10 * 1.05) - 1
    assert pytest.approx(result, rel=1e-6) == expected


def test_total_return_all_losers(losing_trades):
    """Test total return with all losing trades."""
    result = total_return(losing_trades)
    expected = (0.95 * 0.97) - 1
    assert result < 0
    assert pytest.approx(result, rel=1e-6) == expected


def test_annualized_return(sample_trades):
    """Test annualized return calculation."""
    result = annualized_return(sample_trades)
    total_ret = total_return(sample_trades)
    first_entry = sample_trades["entry_date"].min()
    last_exit = sample_trades["exit_date"].max()
    days = (last_exit - first_entry).days
    years = days / 365.0
    expected = (1 + total_ret) ** (1 / years) - 1
    assert pytest.approx(result, rel=1e-6) == expected


def test_annualized_return_short_period():
    """Test annualized return for very short period."""
    trades = pd.DataFrame({
        "entry_date": [datetime(2024, 1, 1)],
        "exit_date": [datetime(2024, 1, 2)],
        "return": [0.01],
    })
    result = annualized_return(trades)
    # Should annualize 1% return over 1 day
    assert result > 0.01  # Annualized should be much higher


def test_sharpe_ratio(sample_trades):
    """Test Sharpe ratio calculation."""
    result = sharpe_ratio(sample_trades)
    assert isinstance(result, float)
    # With mixed returns, Sharpe should be positive but moderate
    assert result > 0


def test_sharpe_ratio_all_winners(winning_trades):
    """Test Sharpe ratio with all winning trades."""
    result = sharpe_ratio(winning_trades)
    # Should have high Sharpe ratio
    assert result > 0


def test_sharpe_ratio_single_trade():
    """Test Sharpe ratio with single trade (should return 0)."""
    trades = pd.DataFrame({
        "entry_date": [datetime(2024, 1, 1)],
        "exit_date": [datetime(2024, 1, 10)],
        "return": [0.05],
    })
    result = sharpe_ratio(trades)
    assert result == 0.0


def test_sharpe_ratio_no_volatility():
    """Test Sharpe ratio with identical returns (zero volatility)."""
    trades = pd.DataFrame({
        "entry_date": [datetime(2024, 1, 1), datetime(2024, 2, 1)],
        "exit_date": [datetime(2024, 1, 10), datetime(2024, 2, 10)],
        "return": [0.05, 0.05],
    })
    result = sharpe_ratio(trades)
    assert result == 0.0


def test_max_drawdown(sample_trades):
    """Test maximum drawdown calculation."""
    result = max_drawdown(sample_trades)
    assert isinstance(result, float)
    assert result <= 0  # Drawdown should be negative or zero


def test_max_drawdown_no_drawdown(winning_trades):
    """Test max drawdown with only winning trades."""
    result = max_drawdown(winning_trades)
    # Should have no drawdown (0 or very small negative)
    assert result <= 0
    assert result >= -0.01


def test_max_drawdown_steep_decline():
    """Test max drawdown with steep decline."""
    trades = pd.DataFrame({
        "entry_date": [
            datetime(2024, 1, 1),
            datetime(2024, 2, 1),
            datetime(2024, 3, 1),
        ],
        "exit_date": [
            datetime(2024, 1, 10),
            datetime(2024, 2, 10),
            datetime(2024, 3, 10),
        ],
        "return": [0.20, -0.15, -0.10],
    })
    result = max_drawdown(trades)
    assert result < -0.20  # Should capture the decline


def test_win_rate(sample_trades):
    """Test win rate calculation."""
    result = win_rate(sample_trades)
    # 3 wins out of 5 trades = 0.6
    expected = 3 / 5
    assert pytest.approx(result, rel=1e-6) == expected


def test_win_rate_all_winners(winning_trades):
    """Test win rate with all winning trades."""
    result = win_rate(winning_trades)
    assert result == 1.0


def test_win_rate_all_losers(losing_trades):
    """Test win rate with all losing trades."""
    result = win_rate(losing_trades)
    assert result == 0.0


def test_profit_factor(sample_trades):
    """Test profit factor calculation."""
    result = profit_factor(sample_trades)
    gross_profit = 0.05 + 0.03 + 0.04  # 0.12
    gross_loss = abs(-0.02 + -0.01)  # 0.03
    expected = gross_profit / gross_loss
    assert pytest.approx(result, rel=1e-6) == expected


def test_profit_factor_all_winners(winning_trades):
    """Test profit factor with all winning trades."""
    result = profit_factor(winning_trades)
    assert result == float("inf")


def test_profit_factor_all_losers(losing_trades):
    """Test profit factor with all losing trades."""
    result = profit_factor(losing_trades)
    assert result == 0.0


def test_num_trades(sample_trades):
    """Test total number of trades."""
    result = num_trades(sample_trades)
    assert result == 5


def test_avg_trade_duration(sample_trades):
    """Test average trade duration calculation."""
    result = avg_trade_duration(sample_trades)
    # Calculate expected manually
    durations = [
        (datetime(2024, 1, 10) - datetime(2024, 1, 1)).days,
        (datetime(2024, 2, 15) - datetime(2024, 2, 1)).days,
        (datetime(2024, 3, 5) - datetime(2024, 3, 1)).days,
        (datetime(2024, 4, 20) - datetime(2024, 4, 1)).days,
        (datetime(2024, 5, 8) - datetime(2024, 5, 1)).days,
    ]
    expected = sum(durations) / len(durations)
    assert pytest.approx(result, rel=1e-6) == expected


def test_calculate_all_metrics(sample_trades):
    """Test integration of all metrics calculation."""
    result = calculate_all(sample_trades)

    # Check all keys are present
    expected_keys = {
        "total_return",
        "annualized_return",
        "sharpe_ratio",
        "max_drawdown",
        "win_rate",
        "profit_factor",
        "num_trades",
        "avg_trade_duration_days",
    }
    assert set(result.keys()) == expected_keys

    # Check values match individual calculations
    assert pytest.approx(result["total_return"], rel=1e-6) == total_return(sample_trades)
    assert pytest.approx(result["annualized_return"], rel=1e-6) == annualized_return(sample_trades)
    assert pytest.approx(result["sharpe_ratio"], rel=1e-6) == sharpe_ratio(sample_trades)
    assert pytest.approx(result["max_drawdown"], rel=1e-6) == max_drawdown(sample_trades)
    assert pytest.approx(result["win_rate"], rel=1e-6) == win_rate(sample_trades)
    assert pytest.approx(result["profit_factor"], rel=1e-6) == profit_factor(sample_trades)
    assert result["num_trades"] == num_trades(sample_trades)
    assert pytest.approx(result["avg_trade_duration_days"], rel=1e-6) == avg_trade_duration(sample_trades)


def test_empty_trades(empty_trades):
    """Test handling of empty DataFrame."""
    # All metrics should handle empty DataFrame gracefully
    assert total_return(empty_trades) == 0.0
    assert annualized_return(empty_trades) == 0.0
    assert sharpe_ratio(empty_trades) == 0.0
    assert max_drawdown(empty_trades) == 0.0
    assert win_rate(empty_trades) == 0.0
    assert profit_factor(empty_trades) == 0.0
    assert num_trades(empty_trades) == 0
    assert avg_trade_duration(empty_trades) == 0.0


def test_empty_trades_calculate_all(empty_trades):
    """Test calculate_all with empty DataFrame."""
    result = calculate_all(empty_trades)

    assert result["total_return"] == 0.0
    assert result["annualized_return"] == 0.0
    assert result["sharpe_ratio"] == 0.0
    assert result["max_drawdown"] == 0.0
    assert result["win_rate"] == 0.0
    assert result["profit_factor"] == 0.0
    assert result["num_trades"] == 0
    assert result["avg_trade_duration_days"] == 0.0
