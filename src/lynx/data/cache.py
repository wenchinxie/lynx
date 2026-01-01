"""Local cache management for price data."""

import warnings
from datetime import date
from pathlib import Path

import pandas as pd

from lynx.data.yahoo import fetch_adjusted_prices


def get_cache_dir() -> Path:
    """Get the cache directory path."""
    cache_dir = Path.home() / ".lynx" / "cache" / "prices"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cache_path(symbol: str) -> Path:
    """Get the cache file path for a symbol."""
    return get_cache_dir() / f"{symbol}.parquet"


def save_to_cache(symbol: str, df: pd.DataFrame) -> None:
    """Save price data to cache."""
    path = get_cache_path(symbol)
    df.to_parquet(path)


def load_from_cache(symbol: str) -> pd.DataFrame | None:
    """Load price data from cache. Returns None if not found."""
    path = get_cache_path(symbol)
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except Exception as e:
        warnings.warn(f"Failed to read cache for {symbol}: {e}")
        return None


def fetch_prices_with_cache(
    symbols: list[str],
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """Fetch prices with local caching support."""
    result_dfs = []
    symbols_to_fetch = []

    for symbol in symbols:
        cached = load_from_cache(symbol)

        if cached is not None and not cached.empty:
            cached_start = cached.index.min().date()
            cached_end = cached.index.max().date()

            if cached_start <= start_date and cached_end >= end_date:
                # Cache covers the range
                mask = (cached.index.date >= start_date) & (cached.index.date <= end_date)
                filtered = cached.loc[mask]
                if filtered.columns[0] != symbol:
                    filtered = filtered.rename(columns={filtered.columns[0]: symbol})
                result_dfs.append(filtered)
            else:
                symbols_to_fetch.append(symbol)
        else:
            symbols_to_fetch.append(symbol)

    if symbols_to_fetch:
        fetched = fetch_adjusted_prices(
            symbols=symbols_to_fetch,
            start_date=start_date,
            end_date=end_date,
        )

        for symbol in symbols_to_fetch:
            if symbol in fetched.columns:
                symbol_df = fetched[[symbol]]

                existing = load_from_cache(symbol)
                if existing is not None and not existing.empty:
                    if existing.columns[0] != symbol:
                        existing = existing.rename(columns={existing.columns[0]: symbol})
                    combined = pd.concat([existing, symbol_df])
                    combined = combined[~combined.index.duplicated(keep="last")]
                    combined = combined.sort_index()
                    save_to_cache(symbol, combined)
                else:
                    save_to_cache(symbol, symbol_df)

                result_dfs.append(symbol_df)

    if not result_dfs:
        return pd.DataFrame()

    result = pd.concat(result_dfs, axis=1)
    result = result.sort_index()
    mask = (result.index.date >= start_date) & (result.index.date <= end_date)
    return result.loc[mask]
