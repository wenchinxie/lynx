"""Yahoo Finance data fetching."""

from datetime import date

import pandas as pd


def fetch_adjusted_prices(
    symbols: list[str],
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """Fetch adjusted close prices from Yahoo Finance.

    Args:
        symbols: List of Yahoo Finance compatible symbols
        start_date: Start date for price data
        end_date: End date for price data

    Returns:
        DataFrame with DatetimeIndex and symbol columns containing adjusted close prices

    Raises:
        DataFetchError: If Yahoo Finance API fails
        InvalidSymbolError: If any symbol is invalid
    """
    raise NotImplementedError
