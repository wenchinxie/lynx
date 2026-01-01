"""Tests for Yahoo Finance data fetching."""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from lynx.data.exceptions import DataFetchError
from lynx.data.yahoo import fetch_adjusted_prices, validate_symbols


class TestValidateSymbols:
    """Tests for symbol validation."""

    @patch("lynx.data.yahoo.yf.Ticker")
    def test_valid_symbol_passes(self, mock_ticker):
        """Valid symbols should pass validation."""
        mock_instance = MagicMock()
        mock_instance.info = {"regularMarketPrice": 100.0}
        mock_ticker.return_value = mock_instance

        result = validate_symbols(["AAPL"])
        assert result.valid_symbols == ["AAPL"]
        assert result.invalid_symbols == []

    @patch("lynx.data.yahoo.yf.Ticker")
    def test_valid_symbol_with_previous_close(self, mock_ticker):
        """Symbol valid if previousClose exists (even without regularMarketPrice)."""
        mock_instance = MagicMock()
        # Symbol without regularMarketPrice but with previousClose (e.g., after hours)
        mock_instance.info = {"previousClose": 150.0, "symbol": "AAPL"}
        mock_ticker.return_value = mock_instance

        result = validate_symbols(["AAPL"])
        assert result.valid_symbols == ["AAPL"]
        assert result.invalid_symbols == []

    @patch("lynx.data.yahoo.yf.Ticker")
    def test_valid_symbol_with_symbol_field_only(self, mock_ticker):
        """Symbol valid if symbol field matches (minimum validation)."""
        mock_instance = MagicMock()
        # Symbol with only symbol field matching
        mock_instance.info = {"symbol": "AAPL"}
        mock_ticker.return_value = mock_instance

        result = validate_symbols(["AAPL"])
        assert result.valid_symbols == ["AAPL"]
        assert result.invalid_symbols == []

    @patch("lynx.data.yahoo.yf.Ticker")
    def test_invalid_symbol_detected(self, mock_ticker):
        """Invalid symbols should be detected."""
        mock_instance = MagicMock()
        mock_instance.info = {}  # Empty info = invalid
        mock_ticker.return_value = mock_instance

        result = validate_symbols(["INVALID123"])
        assert result.valid_symbols == []
        assert result.invalid_symbols == ["INVALID123"]

    @patch("lynx.data.yahoo.yf.Ticker")
    def test_mixed_symbols(self, mock_ticker):
        """Mix of valid and invalid symbols."""
        def side_effect(symbol):
            mock = MagicMock()
            if symbol == "AAPL":
                mock.info = {"regularMarketPrice": 100.0}
            else:
                mock.info = {}
            return mock

        mock_ticker.side_effect = side_effect

        result = validate_symbols(["AAPL", "INVALID"])
        assert result.valid_symbols == ["AAPL"]
        assert result.invalid_symbols == ["INVALID"]


class TestFetchAdjustedPrices:
    """Tests for price fetching."""

    def test_empty_symbols_raises_error(self):
        """Empty symbols list should raise ValueError."""
        with pytest.raises(ValueError, match="symbols list cannot be empty"):
            fetch_adjusted_prices(
                symbols=[],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 3),
            )

    def test_start_after_end_raises_error(self):
        """Start date after end date should raise ValueError."""
        with pytest.raises(ValueError, match="start_date.*must be before end_date"):
            fetch_adjusted_prices(
                symbols=["AAPL"],
                start_date=date(2024, 1, 10),
                end_date=date(2024, 1, 1),
            )

    @patch("lynx.data.yahoo.yf.download")
    def test_fetch_single_symbol(self, mock_download):
        """Fetch prices for single symbol."""
        mock_df = pd.DataFrame(
            {"Adj Close": [100.0, 101.0, 102.0]},
            index=pd.date_range("2024-01-01", periods=3),
        )
        mock_download.return_value = mock_df

        result = fetch_adjusted_prices(
            symbols=["AAPL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
        )

        assert isinstance(result, pd.DataFrame)
        assert "AAPL" in result.columns
        assert len(result) == 3

    @patch("lynx.data.yahoo.yf.download")
    def test_fetch_multiple_symbols(self, mock_download):
        """Fetch prices for multiple symbols."""
        mock_df = pd.DataFrame(
            {
                ("Adj Close", "AAPL"): [100.0, 101.0],
                ("Adj Close", "MSFT"): [200.0, 201.0],
            },
            index=pd.date_range("2024-01-01", periods=2),
        )
        mock_df.columns = pd.MultiIndex.from_tuples(mock_df.columns)
        mock_download.return_value = mock_df

        result = fetch_adjusted_prices(
            symbols=["AAPL", "MSFT"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
        )

        assert "AAPL" in result.columns
        assert "MSFT" in result.columns

    @patch("lynx.data.yahoo.yf.download")
    def test_fetch_failure_raises_error(self, mock_download):
        """Network failure should raise DataFetchError."""
        mock_download.side_effect = Exception("Network error")

        with pytest.raises(DataFetchError):
            fetch_adjusted_prices(
                symbols=["AAPL"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 3),
            )

    @patch("lynx.data.yahoo.yf.download")
    def test_empty_result_raises_error(self, mock_download):
        """Empty result should raise DataFetchError."""
        mock_download.return_value = pd.DataFrame()

        with pytest.raises(DataFetchError):
            fetch_adjusted_prices(
                symbols=["AAPL"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 3),
            )
