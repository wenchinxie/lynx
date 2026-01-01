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

            # Check if we got valid info back by checking multiple fields
            # Note: regularMarketPrice is real-time and may be None outside trading hours,
            # so we check multiple fields to verify symbol existence
            if info and any([
                info.get("regularMarketPrice") is not None,
                info.get("previousClose") is not None,
                info.get("symbol") == symbol,  # At least confirm symbol exists
            ]):
                result.valid_symbols.append(symbol)
            else:
                result.invalid_symbols.append(symbol)
                result.errors[symbol] = "Symbol not found or no market data"
        except Exception as e:
            # Broad exception handling is acceptable here since yfinance can throw
            # various exception types (network errors, API errors, etc.)
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
        ValueError: If input validation fails
    """
    # Input validation
    if not symbols:
        raise ValueError("symbols list cannot be empty")
    if start_date > end_date:
        raise ValueError(f"start_date {start_date} must be before end_date {end_date}")

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
