"""Test to verify all fixtures are working correctly."""


import pandas as pd


def test_temp_data_dir(temp_data_dir):
    """Test that temp_data_dir fixture creates a directory."""
    assert temp_data_dir.exists()
    assert temp_data_dir.is_dir()
    assert temp_data_dir.name == "lynx_data"


def test_sample_trades_df(sample_trades_df):
    """Test that sample_trades_df fixture returns correct DataFrame."""
    assert isinstance(sample_trades_df, pd.DataFrame)
    assert len(sample_trades_df) == 5
    assert list(sample_trades_df.columns) == [
        "symbol", "entry_date", "exit_date",
        "entry_price", "exit_price", "return"
    ]
    assert sample_trades_df["symbol"].dtype == object
    assert pd.api.types.is_datetime64_any_dtype(sample_trades_df["entry_date"])
    assert pd.api.types.is_datetime64_any_dtype(sample_trades_df["exit_date"])


def test_sample_signal_df(sample_signal_df):
    """Test that sample_signal_df fixture returns correct DataFrame."""
    assert isinstance(sample_signal_df, pd.DataFrame)
    assert len(sample_signal_df) == 10
    assert list(sample_signal_df.columns) == ["2330", "2317", "2454"]
    assert sample_signal_df["2330"].dtype == bool
    assert pd.api.types.is_datetime64_any_dtype(sample_signal_df.index)


def test_sample_price_df(sample_price_df):
    """Test that sample_price_df fixture returns correct DataFrame."""
    assert isinstance(sample_price_df, pd.DataFrame)
    assert len(sample_price_df) == 10
    assert list(sample_price_df.columns) == ["2330", "2317", "2454"]
    assert sample_price_df["2330"].dtype == float
    assert pd.api.types.is_datetime64_any_dtype(sample_price_df.index)


def test_empty_trades_df(empty_trades_df):
    """Test that empty_trades_df fixture returns empty DataFrame with correct schema."""
    assert isinstance(empty_trades_df, pd.DataFrame)
    assert len(empty_trades_df) == 0
    assert list(empty_trades_df.columns) == [
        "symbol", "entry_date", "exit_date",
        "entry_price", "exit_price", "return"
    ]
    assert empty_trades_df["symbol"].dtype == object
    assert pd.api.types.is_datetime64_any_dtype(empty_trades_df["entry_date"])
    assert pd.api.types.is_datetime64_any_dtype(empty_trades_df["exit_date"])
    assert empty_trades_df["entry_price"].dtype == float
