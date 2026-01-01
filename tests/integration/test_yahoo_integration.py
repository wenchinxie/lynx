"""Real integration tests with Yahoo Finance API.

These tests make actual network calls and are skipped by default.
Run with: pytest tests/integration/test_yahoo_integration.py --run-integration
"""

import pytest

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestYahooFinanceIntegration:
    """Real Yahoo Finance API tests."""

    def test_fetch_real_prices(self):
        """Test fetching real prices from Yahoo Finance."""
        from datetime import date
        from lynx.data.yahoo import fetch_adjusted_prices

        prices = fetch_adjusted_prices(
            symbols=["AAPL"],
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 10),
        )

        assert not prices.empty
        assert "AAPL" in prices.columns
        assert len(prices) > 0

    def test_validate_real_symbols(self):
        """Test validating real symbols."""
        from lynx.data.yahoo import validate_symbols

        result = validate_symbols(["AAPL", "INVALID_SYMBOL_XYZ123"])

        assert "AAPL" in result.valid_symbols
        assert "INVALID_SYMBOL_XYZ123" in result.invalid_symbols

    def test_fetch_taiwan_stock(self):
        """Test fetching Taiwan stock (2330.TW = TSMC)."""
        from datetime import date
        from lynx.data.yahoo import fetch_adjusted_prices

        prices = fetch_adjusted_prices(
            symbols=["2330.TW"],
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 10),
        )

        assert not prices.empty
        assert "2330.TW" in prices.columns
