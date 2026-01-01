"""Tests for backtest auto-fetch functionality."""

from unittest.mock import patch

import pandas as pd
import pytest

from lynx.backtest.engine import BacktestEngine
from lynx.data.exceptions import InvalidSymbolError
from lynx.data.yahoo import ValidationResult


class TestBacktestAutoFetch:
    """Tests for auto-fetching prices in backtest."""

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
    def test_auto_fetch_when_price_not_provided(
        self, mock_fetch, mock_validate, entry_signal, exit_signal, mock_prices
    ):
        """Should auto-fetch prices when not provided."""
        mock_validate.return_value = ValidationResult(valid_symbols=["AAPL"], invalid_symbols=[])
        mock_fetch.return_value = mock_prices

        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=None,
            initial_capital=1_000_000,
            auto_fetch_prices=True,
        )
        engine.run()

        mock_validate.assert_called_once()
        mock_fetch.assert_called_once()

    def test_uses_provided_prices(self, entry_signal, exit_signal, mock_prices):
        """Should use provided prices without fetching."""
        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=mock_prices,
            initial_capital=1_000_000,
        )
        engine.run()
        assert len(engine.trades) > 0

    @patch("lynx.data.yahoo.validate_symbols")
    def test_raises_on_invalid_symbols(self, mock_validate, entry_signal, exit_signal):
        """Should raise InvalidSymbolError for invalid symbols."""
        mock_validate.return_value = ValidationResult(
            valid_symbols=[], invalid_symbols=["AAPL"], errors={"AAPL": "Not found"}
        )

        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=None,
            initial_capital=1_000_000,
        )

        with pytest.raises(InvalidSymbolError):
            engine.run()

    def test_auto_fetch_disabled_requires_price(self, entry_signal, exit_signal):
        """Should raise error when auto_fetch=False and no price."""
        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=None,
            initial_capital=1_000_000,
            auto_fetch_prices=False,
        )
        with pytest.raises(ValueError, match="price.*required"):
            engine.run()
