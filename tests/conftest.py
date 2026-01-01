# tests/conftest.py
"""Shared fixtures for lynx tests."""


import pandas as pd
import pytest


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Create a temporary data directory for tests and configure lynx to use it."""
    data_dir = tmp_path / "lynx_data"
    data_dir.mkdir()

    # Set the data directory for the test
    monkeypatch.setenv("LYNX_DATA_DIR", str(data_dir))

    # Also update the config module
    from lynx import config
    config(data_dir=data_dir)

    return data_dir


@pytest.fixture
def sample_trades_df():
    """Create a sample trades DataFrame for testing."""
    return pd.DataFrame({
        "symbol": ["2330", "2317", "2454", "2330", "2317"],
        "entry_date": pd.to_datetime([
            "2024-01-02", "2024-01-03", "2024-01-05",
            "2024-01-10", "2024-01-12"
        ]),
        "exit_date": pd.to_datetime([
            "2024-01-05", "2024-01-08", "2024-01-10",
            "2024-01-15", "2024-01-18"
        ]),
        "entry_price": [580.0, 45.0, 125.0, 590.0, 46.0],
        "exit_price": [595.0, 44.0, 130.0, 600.0, 48.0],
        "return": [0.0259, -0.0222, 0.04, 0.0169, 0.0435],
    })


@pytest.fixture
def sample_signal_df():
    """Create a sample signal DataFrame for testing."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "2330": [True, False, True, True, False, True, False, True, False, True],
        "2317": [False, True, True, False, True, False, True, False, True, False],
        "2454": [True, True, False, True, True, False, False, True, True, False],
    }, index=dates)


@pytest.fixture
def sample_price_df():
    """Create a sample price DataFrame for testing."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "2330": [580.0, 582.0, 585.0, 590.0, 588.0, 592.0, 595.0, 598.0, 600.0, 602.0],
        "2317": [45.0, 44.8, 45.2, 45.5, 44.9, 46.0, 45.8, 46.2, 46.5, 47.0],
        "2454": [125.0, 126.0, 127.0, 125.5, 128.0, 129.0, 130.0, 128.5, 131.0, 132.0],
    }, index=dates)


@pytest.fixture
def empty_trades_df():
    """Create an empty trades DataFrame with correct schema."""
    return pd.DataFrame({
        "symbol": pd.Series([], dtype=str),
        "entry_date": pd.Series([], dtype="datetime64[ns]"),
        "exit_date": pd.Series([], dtype="datetime64[ns]"),
        "entry_price": pd.Series([], dtype=float),
        "exit_price": pd.Series([], dtype=float),
        "return": pd.Series([], dtype=float),
    })


# Backtest fixtures

@pytest.fixture
def sample_entry_signal():
    """Create a sample entry signal DataFrame for backtesting."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "2330.TW": [0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
        "2317.TW": [0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
    }, index=dates)


@pytest.fixture
def sample_exit_signal():
    """Create a sample exit signal DataFrame for backtesting."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "2330.TW": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        "2317.TW": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    }, index=dates)


@pytest.fixture
def sample_backtest_price():
    """Create a sample price DataFrame for backtesting."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "2330.TW": [580.0, 585.0, 590.0, 600.0, 595.0, 600.0, 605.0, 610.0, 615.0, 620.0],
        "2317.TW": [112.0, 113.0, 114.0, 116.0, 115.0, 116.0, 117.0, 118.0, 119.0, 120.0],
    }, index=dates)
