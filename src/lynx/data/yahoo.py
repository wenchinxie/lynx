"""Yahoo Finance data fetching."""

from dataclasses import dataclass, field
from datetime import date

import pandas as pd
import yfinance as yf

from lynx.data.exceptions import DataFetchError


@dataclass
class ValidationResult:
    """Result of symbol validation."""

    valid_symbols: list[str] = field(default_factory=list)
    invalid_symbols: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


def validate_symbols(symbols: list[str]) -> ValidationResult:
    """Validate that symbols exist on Yahoo Finance.

    Args:
        symbols: List of symbols to validate

    Returns:
        ValidationResult with valid/invalid symbols and error messages
    """
    result = ValidationResult()

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Check if we got valid info back
            if info and info.get("regularMarketPrice") is not None:
                result.valid_symbols.append(symbol)
            else:
                result.invalid_symbols.append(symbol)
                result.errors[symbol] = "Symbol not found or no market data"
        except Exception as e:
            result.invalid_symbols.append(symbol)
            result.errors[symbol] = str(e)

    return result


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
    try:
        # Download data from Yahoo Finance
        data = yf.download(
            tickers=symbols,
            start=start_date,
            end=end_date,
            auto_adjust=False,  # Keep Adj Close separate
            progress=False,
        )

        if data.empty:
            raise DataFetchError(f"No data returned for symbols: {symbols}")

        # Extract Adj Close column(s)
        if len(symbols) == 1:
            # Single symbol: data has simple column names
            if "Adj Close" in data.columns:
                result = data[["Adj Close"]].copy()
                result.columns = symbols
            else:
                raise DataFetchError(f"No Adj Close data for {symbols[0]}")
        else:
            # Multiple symbols: data has MultiIndex columns
            if "Adj Close" in data.columns.get_level_values(0):
                result = data["Adj Close"].copy()
            else:
                raise DataFetchError("No Adj Close data in response")

        return result

    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Failed to fetch data: {e}") from e
