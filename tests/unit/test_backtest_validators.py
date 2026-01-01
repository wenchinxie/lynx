"""Tests for backtest input validation."""

import pandas as pd
import pytest

from lynx.backtest.validators import validate_backtest_inputs
from lynx.exceptions import ValidationError


@pytest.fixture
def valid_entry_signal():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame({
        "2330.TW": [0.5, 0.0, 0.3, 0.0, 0.0],
        "2317.TW": [0.5, 0.0, 0.7, 0.0, 0.0],
    }, index=dates)


@pytest.fixture
def valid_exit_signal():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame({
        "2330.TW": [0.0, 0.0, 0.0, 1.0, 0.0],
        "2317.TW": [0.0, 0.0, 0.0, 0.5, 0.0],
    }, index=dates)


@pytest.fixture
def valid_price():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame({
        "2330.TW": [580.0, 582.0, 585.0, 590.0, 588.0],
        "2317.TW": [112.0, 113.0, 114.0, 115.0, 114.5],
    }, index=dates)


class TestValidateBacktestInputs:
    def test_valid_inputs_pass(self, valid_entry_signal, valid_exit_signal, valid_price):
        # Should not raise
        validate_backtest_inputs(valid_entry_signal, valid_exit_signal, valid_price)

    def test_entry_signal_not_dataframe_raises(self, valid_exit_signal, valid_price):
        with pytest.raises(ValidationError, match="entry_signal must be a DataFrame"):
            validate_backtest_inputs([1, 2, 3], valid_exit_signal, valid_price)

    def test_exit_signal_not_dataframe_raises(self, valid_entry_signal, valid_price):
        with pytest.raises(ValidationError, match="exit_signal must be a DataFrame"):
            validate_backtest_inputs(valid_entry_signal, "not a df", valid_price)

    def test_price_not_dataframe_raises(self, valid_entry_signal, valid_exit_signal):
        with pytest.raises(ValidationError, match="price must be a DataFrame"):
            validate_backtest_inputs(valid_entry_signal, valid_exit_signal, None)

    def test_mismatched_columns_raises(self, valid_entry_signal, valid_exit_signal, valid_price):
        # Add extra column to entry_signal
        entry_with_extra = valid_entry_signal.copy()
        entry_with_extra["EXTRA"] = 0.0
        with pytest.raises(ValidationError, match="columns must match"):
            validate_backtest_inputs(entry_with_extra, valid_exit_signal, valid_price)

    def test_entry_signal_values_out_of_range_raises(self, valid_exit_signal, valid_price):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        bad_entry = pd.DataFrame({
            "2330.TW": [1.5, 0.0, 0.0, 0.0, 0.0],  # > 1.0
            "2317.TW": [0.0, 0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        with pytest.raises(ValidationError, match="entry_signal values must be between 0 and 1"):
            validate_backtest_inputs(bad_entry, valid_exit_signal, valid_price)

    def test_exit_signal_values_out_of_range_raises(self, valid_entry_signal, valid_price):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        bad_exit = pd.DataFrame({
            "2330.TW": [-0.1, 0.0, 0.0, 0.0, 0.0],  # < 0
            "2317.TW": [0.0, 0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        with pytest.raises(ValidationError, match="exit_signal values must be between 0 and 1"):
            validate_backtest_inputs(valid_entry_signal, bad_exit, valid_price)

    def test_price_with_negative_values_raises(self, valid_entry_signal, valid_exit_signal):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        bad_price = pd.DataFrame({
            "2330.TW": [580.0, -1.0, 585.0, 590.0, 588.0],
            "2317.TW": [112.0, 113.0, 114.0, 115.0, 114.5],
        }, index=dates)
        with pytest.raises(ValidationError, match="price values must be positive"):
            validate_backtest_inputs(valid_entry_signal, valid_exit_signal, bad_price)

    def test_empty_price_raises(self, valid_entry_signal, valid_exit_signal):
        empty_price = pd.DataFrame()
        with pytest.raises(ValidationError, match="price DataFrame cannot be empty"):
            validate_backtest_inputs(valid_entry_signal, valid_exit_signal, empty_price)
