"""Tests for price data caching."""

from datetime import date
from unittest.mock import patch

import pandas as pd

from lynx.data.cache import (
    fetch_prices_with_cache,
    get_cache_dir,
    get_cache_path,
    load_from_cache,
    save_to_cache,
)


class TestCacheDir:
    """Tests for cache directory management."""

    def test_get_cache_dir_creates_directory(self, tmp_path):
        """Cache directory should be created if it doesn't exist."""
        with patch("lynx.data.cache.Path.home", return_value=tmp_path):
            cache_dir = get_cache_dir()
            assert cache_dir.exists()
            assert cache_dir == tmp_path / ".lynx" / "cache" / "prices"

    def test_get_cache_path(self, tmp_path):
        """Cache path should be based on symbol."""
        with patch("lynx.data.cache.Path.home", return_value=tmp_path):
            path = get_cache_path("2330.TW")
            assert path.name == "2330.TW.parquet"


class TestCacheOperations:
    """Tests for cache read/write operations."""

    def test_save_and_load_cache(self, tmp_path):
        """Should be able to save and load cached data."""
        with patch("lynx.data.cache.Path.home", return_value=tmp_path):
            df = pd.DataFrame(
                {"close": [100.0, 101.0]},
                index=pd.date_range("2024-01-01", periods=2),
            )

            save_to_cache("AAPL", df)
            loaded = load_from_cache("AAPL")

            pd.testing.assert_frame_equal(df, loaded, check_freq=False)

    def test_load_nonexistent_cache_returns_none(self, tmp_path):
        """Loading non-existent cache should return None."""
        with patch("lynx.data.cache.Path.home", return_value=tmp_path):
            result = load_from_cache("NONEXISTENT")
            assert result is None


class TestFetchWithCache:
    """Tests for cached fetching."""

    @patch("lynx.data.cache.fetch_adjusted_prices")
    def test_fetches_when_no_cache(self, mock_fetch, tmp_path):
        """Should fetch from API when no cache exists."""
        with patch("lynx.data.cache.Path.home", return_value=tmp_path):
            mock_df = pd.DataFrame(
                {"AAPL": [100.0, 101.0]},
                index=pd.date_range("2024-01-01", periods=2),
            )
            mock_fetch.return_value = mock_df

            result = fetch_prices_with_cache(
                symbols=["AAPL"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 2),
            )

            mock_fetch.assert_called_once()
            assert "AAPL" in result.columns

    @patch("lynx.data.cache.fetch_adjusted_prices")
    def test_uses_cache_when_available(self, mock_fetch, tmp_path):
        """Should use cache when data is available."""
        with patch("lynx.data.cache.Path.home", return_value=tmp_path):
            # Pre-populate cache
            cached_df = pd.DataFrame(
                {"close": [100.0, 101.0]},
                index=pd.date_range("2024-01-01", periods=2),
            )
            save_to_cache("AAPL", cached_df)

            fetch_prices_with_cache(
                symbols=["AAPL"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 2),
            )

            # Should not call API since cache covers the range
            mock_fetch.assert_not_called()

    @patch("lynx.data.cache.fetch_adjusted_prices")
    def test_fetches_missing_dates(self, mock_fetch, tmp_path):
        """Should fetch only missing date ranges."""
        with patch("lynx.data.cache.Path.home", return_value=tmp_path):
            # Pre-populate cache with partial data
            cached_df = pd.DataFrame(
                {"close": [100.0]},
                index=pd.date_range("2024-01-01", periods=1),
            )
            save_to_cache("AAPL", cached_df)

            # Mock returns new data
            mock_df = pd.DataFrame(
                {"AAPL": [101.0, 102.0]},
                index=pd.date_range("2024-01-02", periods=2),
            )
            mock_fetch.return_value = mock_df

            fetch_prices_with_cache(
                symbols=["AAPL"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 3),
            )

            # Should have called API for missing dates
            mock_fetch.assert_called_once()
