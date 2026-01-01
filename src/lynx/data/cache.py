"""Local cache management for price data."""

from datetime import date
from pathlib import Path

import pandas as pd


def get_cache_dir() -> Path:
    """Get the cache directory path."""
    cache_dir = Path.home() / ".lynx" / "cache" / "prices"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def fetch_prices_with_cache(
    symbols: list[str],
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """Fetch prices with local caching support.

    Args:
        symbols: List of symbols to fetch
        start_date: Start date
        end_date: End date

    Returns:
        DataFrame with DatetimeIndex and symbol columns
    """
    raise NotImplementedError
