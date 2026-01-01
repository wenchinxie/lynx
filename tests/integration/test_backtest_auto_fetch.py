"""Integration tests for backtest auto-fetch functionality."""

from unittest.mock import patch

import pandas as pd
import pytest

import lynx
from lynx.data.yahoo import ValidationResult


class TestBacktestAPIAutoFetch:
    """Integration tests for lynx.backtest() with auto-fetch."""

    @pytest.fixture
    def entry_signal(self):
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        return pd.DataFrame({"AAPL": [1, 0, 0, 0, 0]}, index=dates)

    @pytest.fixture
    def exit_signal(self):
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        return pd.DataFrame({"AAPL": [0, 0, 1, 0, 0]}, index=dates)

    @pytest.fixture
    def mock_prices(self):
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        return pd.DataFrame({"AAPL": [150.0, 151.0, 152.0, 153.0, 154.0]}, index=dates)

    @patch("lynx.data.yahoo.validate_symbols")
    @patch("lynx.data.cache.fetch_prices_with_cache")
    def test_backtest_without_price_parameter(
        self, mock_fetch, mock_validate, entry_signal, exit_signal, mock_prices
    ):
        """lynx.backtest() should work without price parameter."""
        mock_validate.return_value = ValidationResult(valid_symbols=["AAPL"], invalid_symbols=[])
        mock_fetch.return_value = mock_prices

        run = lynx.backtest(
            strategy_name="test_auto_fetch",
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            initial_capital=100_000,
        )

        assert run is not None
        mock_fetch.assert_called_once()

    def test_backtest_with_price_parameter(self, entry_signal, exit_signal, mock_prices):
        """lynx.backtest() should use provided prices."""
        run = lynx.backtest(
            strategy_name="test_with_prices",
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=mock_prices,
            initial_capital=100_000,
        )

        assert run is not None
