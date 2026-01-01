# Auto Fetch Adjusted Prices Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Use superpowers:test-driven-development for each task.

**Goal:** Enable backtest engine to automatically fetch backward-adjusted prices from Yahoo Finance so users only need to provide signals.

**Architecture:** New `lynx.data` module handles Yahoo Finance API calls and local Parquet caching. BacktestEngine is modified to auto-fetch prices when not provided. Symbol validation occurs before fetching.

**Tech Stack:** Python 3.13, yfinance, pandas, pyarrow (for Parquet)

---

## Task 1: Add yfinance Dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add yfinance to dependencies**

Add to `pyproject.toml` under `[project.dependencies]`:

```toml
"yfinance>=0.2.0",
```

**Step 2: Install dependency**

Run: `uv sync`
Expected: Successfully installed yfinance

**Step 3: Verify installation**

Run: `source .venv/bin/activate && python -c "import yfinance; print(yfinance.__version__)"`
Expected: Version number printed (e.g., "0.2.x")

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add yfinance dependency for price fetching"
```

---

## Task 2: Create Data Module Structure

**Files:**
- Create: `src/lynx/data/__init__.py`
- Create: `src/lynx/data/yahoo.py`
- Create: `src/lynx/data/cache.py`
- Create: `src/lynx/data/exceptions.py`

**Step 1: Create module directory**

Run: `mkdir -p src/lynx/data`

**Step 2: Create exceptions.py**

```python
"""Data module exceptions."""


class DataFetchError(Exception):
    """Raised when data fetching fails."""

    pass


class InvalidSymbolError(Exception):
    """Raised when symbol is not found or invalid."""

    pass
```

**Step 3: Create empty yahoo.py**

```python
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
```

**Step 4: Create empty cache.py**

```python
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
```

**Step 5: Create __init__.py**

```python
"""Data fetching and caching module."""

from lynx.data.cache import fetch_prices_with_cache, get_cache_dir
from lynx.data.exceptions import DataFetchError, InvalidSymbolError
from lynx.data.yahoo import fetch_adjusted_prices

__all__ = [
    "fetch_adjusted_prices",
    "fetch_prices_with_cache",
    "get_cache_dir",
    "DataFetchError",
    "InvalidSymbolError",
]
```

**Step 6: Commit**

```bash
git add src/lynx/data/
git commit -m "feat(data): add data module skeleton for price fetching"
```

---

## Task 3: Implement Yahoo Finance Fetching (TDD)

**Files:**
- Create: `tests/unit/test_data_yahoo.py`
- Modify: `src/lynx/data/yahoo.py`

**Step 1: Write failing tests**

Create `tests/unit/test_data_yahoo.py`:

```python
"""Tests for Yahoo Finance data fetching."""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from lynx.data.exceptions import DataFetchError, InvalidSymbolError
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
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/unit/test_data_yahoo.py -v`
Expected: FAIL (NotImplementedError or AttributeError)

**Step 3: Implement yahoo.py**

```python
"""Yahoo Finance data fetching."""

from dataclasses import dataclass, field
from datetime import date

import pandas as pd
import yfinance as yf

from lynx.data.exceptions import DataFetchError, InvalidSymbolError


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
```

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/unit/test_data_yahoo.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/lynx/data/yahoo.py tests/unit/test_data_yahoo.py
git commit -m "feat(data): implement Yahoo Finance price fetching with validation"
```

---

## Task 4: Implement Cache Module (TDD)

**Files:**
- Create: `tests/unit/test_data_cache.py`
- Modify: `src/lynx/data/cache.py`

**Step 1: Write failing tests**

Create `tests/unit/test_data_cache.py`:

```python
"""Tests for price data caching."""

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

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

            pd.testing.assert_frame_equal(df, loaded)

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

            result = fetch_prices_with_cache(
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

            result = fetch_prices_with_cache(
                symbols=["AAPL"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 3),
            )

            # Should have called API for missing dates
            mock_fetch.assert_called_once()
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/unit/test_data_cache.py -v`
Expected: FAIL

**Step 3: Implement cache.py**

```python
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
    """Save price data to cache.

    Args:
        symbol: Stock symbol
        df: DataFrame with DatetimeIndex
    """
    path = get_cache_path(symbol)
    df.to_parquet(path)


def load_from_cache(symbol: str) -> pd.DataFrame | None:
    """Load price data from cache.

    Args:
        symbol: Stock symbol

    Returns:
        DataFrame if cache exists, None otherwise
    """
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
    """Fetch prices with local caching support.

    Args:
        symbols: List of symbols to fetch
        start_date: Start date
        end_date: End date

    Returns:
        DataFrame with DatetimeIndex and symbol columns
    """
    result_dfs = []
    symbols_to_fetch = []
    fetch_ranges: dict[str, tuple[date, date]] = {}

    for symbol in symbols:
        cached = load_from_cache(symbol)

        if cached is not None and not cached.empty:
            cached_start = cached.index.min().date()
            cached_end = cached.index.max().date()

            # Check if cache covers the requested range
            if cached_start <= start_date and cached_end >= end_date:
                # Cache is sufficient
                mask = (cached.index.date >= start_date) & (cached.index.date <= end_date)
                filtered = cached.loc[mask]
                # Rename column to symbol if needed
                if filtered.columns[0] != symbol:
                    filtered = filtered.rename(columns={filtered.columns[0]: symbol})
                result_dfs.append(filtered)
            else:
                # Need to fetch missing data
                symbols_to_fetch.append(symbol)
                # Determine what range to fetch
                fetch_start = min(start_date, cached_start)
                fetch_end = max(end_date, cached_end)
                fetch_ranges[symbol] = (fetch_start, fetch_end)
        else:
            symbols_to_fetch.append(symbol)
            fetch_ranges[symbol] = (start_date, end_date)

    # Fetch missing data
    if symbols_to_fetch:
        # For simplicity, fetch the full requested range for all missing symbols
        fetched = fetch_adjusted_prices(
            symbols=symbols_to_fetch,
            start_date=start_date,
            end_date=end_date,
        )

        # Save to cache and add to results
        for symbol in symbols_to_fetch:
            if symbol in fetched.columns:
                symbol_df = fetched[[symbol]]

                # Merge with existing cache if any
                existing = load_from_cache(symbol)
                if existing is not None and not existing.empty:
                    # Rename existing column to match
                    if existing.columns[0] != symbol:
                        existing = existing.rename(columns={existing.columns[0]: symbol})
                    combined = pd.concat([existing, symbol_df])
                    combined = combined[~combined.index.duplicated(keep="last")]
                    combined = combined.sort_index()
                    save_to_cache(symbol, combined)
                else:
                    save_to_cache(symbol, symbol_df)

                result_dfs.append(symbol_df)

    # Combine all results
    if not result_dfs:
        return pd.DataFrame()

    result = pd.concat(result_dfs, axis=1)
    result = result.sort_index()

    # Filter to requested date range
    mask = (result.index.date >= start_date) & (result.index.date <= end_date)
    result = result.loc[mask]

    return result
```

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/unit/test_data_cache.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/lynx/data/cache.py tests/unit/test_data_cache.py
git commit -m "feat(data): implement local Parquet caching for price data"
```

---

## Task 5: Update Backtest Engine for Auto-Fetch (TDD)

**Files:**
- Create: `tests/unit/test_backtest_auto_fetch.py`
- Modify: `src/lynx/backtest/engine.py`

**Step 1: Write failing tests**

Create `tests/unit/test_backtest_auto_fetch.py`:

```python
"""Tests for backtest auto-fetch functionality."""

from datetime import date
from unittest.mock import patch

import pandas as pd
import pytest

from lynx.backtest.engine import BacktestEngine, backtest
from lynx.data.exceptions import InvalidSymbolError


class TestBacktestAutoFetch:
    """Tests for auto-fetching prices in backtest."""

    @pytest.fixture
    def signals_df(self):
        """Sample signals DataFrame."""
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        return pd.DataFrame(
            {
                "2330.TW": [1, 0, 0, 0, 1],
            },
            index=dates,
        )

    @pytest.fixture
    def exit_signals_df(self):
        """Sample exit signals DataFrame."""
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        return pd.DataFrame(
            {
                "2330.TW": [0, 0, 1, 0, 0],
            },
            index=dates,
        )

    @pytest.fixture
    def mock_prices(self):
        """Mock price data."""
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        return pd.DataFrame(
            {
                "2330.TW": [100.0, 101.0, 102.0, 103.0, 104.0],
            },
            index=dates,
        )

    @patch("lynx.backtest.engine.validate_symbols")
    @patch("lynx.backtest.engine.fetch_prices_with_cache")
    def test_auto_fetch_when_price_not_provided(
        self, mock_fetch, mock_validate, signals_df, exit_signals_df, mock_prices
    ):
        """Should auto-fetch prices when not provided."""
        from lynx.data.yahoo import ValidationResult

        mock_validate.return_value = ValidationResult(
            valid_symbols=["2330.TW"],
            invalid_symbols=[],
        )
        mock_fetch.return_value = mock_prices

        engine = BacktestEngine(
            entry_signal=signals_df,
            exit_signal=exit_signals_df,
            price=None,  # Not provided
            initial_capital=1_000_000,
            auto_fetch_prices=True,
        )
        engine.run()

        mock_validate.assert_called_once()
        mock_fetch.assert_called_once()

    def test_uses_provided_prices_when_given(self, signals_df, exit_signals_df, mock_prices):
        """Should use provided prices, not fetch."""
        engine = BacktestEngine(
            entry_signal=signals_df,
            exit_signal=exit_signals_df,
            price=mock_prices,  # Provided
            initial_capital=1_000_000,
            auto_fetch_prices=True,  # Should be ignored
        )

        # Should work without network calls
        engine.run()
        assert len(engine.trades) > 0

    @patch("lynx.backtest.engine.validate_symbols")
    def test_raises_on_invalid_symbols(self, mock_validate, signals_df, exit_signals_df):
        """Should raise InvalidSymbolError for invalid symbols."""
        from lynx.data.yahoo import ValidationResult

        mock_validate.return_value = ValidationResult(
            valid_symbols=[],
            invalid_symbols=["2330.TW"],
            errors={"2330.TW": "Not found"},
        )

        engine = BacktestEngine(
            entry_signal=signals_df,
            exit_signal=exit_signals_df,
            price=None,
            initial_capital=1_000_000,
            auto_fetch_prices=True,
        )

        with pytest.raises(InvalidSymbolError):
            engine.run()

    def test_auto_fetch_disabled_requires_price(self, signals_df, exit_signals_df):
        """Should raise error when auto_fetch=False and no price provided."""
        with pytest.raises(ValueError, match="price.*required"):
            BacktestEngine(
                entry_signal=signals_df,
                exit_signal=exit_signals_df,
                price=None,
                initial_capital=1_000_000,
                auto_fetch_prices=False,
            )
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/unit/test_backtest_auto_fetch.py -v`
Expected: FAIL

**Step 3: Modify engine.py to add auto_fetch_prices parameter**

Update `BacktestEngine.__init__()` in `src/lynx/backtest/engine.py`:

```python
def __init__(
    self,
    entry_signal: pd.DataFrame,
    exit_signal: pd.DataFrame,
    price: pd.DataFrame | None,  # Now optional
    initial_capital: float,
    stop_loss: float | None = None,
    take_profit: float | None = None,
    conflict_mode: ConflictMode = "exit_first",
    fees: dict[str, dict[str, float]] | None = None,
    lot_size: dict[str, int] | None = None,
    auto_fetch_prices: bool = True,  # New parameter
):
    """Initialize backtest engine.

    Args:
        entry_signal: Entry signal DataFrame (0-1 values)
        exit_signal: Exit signal DataFrame (0-1 values)
        price: Close price DataFrame (optional if auto_fetch_prices=True)
        initial_capital: Starting capital
        stop_loss: Stop loss percentage (e.g., 0.05 for 5%)
        take_profit: Take profit percentage (e.g., 0.10 for 10%)
        conflict_mode: How to handle entry/exit conflicts
        fees: Custom fee configuration
        lot_size: Custom lot size configuration
        auto_fetch_prices: Auto-fetch prices from Yahoo Finance if not provided
    """
    if price is None and not auto_fetch_prices:
        raise ValueError("price is required when auto_fetch_prices=False")

    self.entry_signal = entry_signal
    self.exit_signal = exit_signal
    self.price = price
    self.initial_capital = initial_capital
    self.stop_loss = stop_loss
    self.take_profit = take_profit
    self.conflict_mode = conflict_mode
    self.custom_fees = fees
    self.custom_lot_size = lot_size
    self.auto_fetch_prices = auto_fetch_prices

    # State
    self.cash = initial_capital
    self.positions: dict[str, Position] = {}
    self.trades: list[dict] = []
    self.equity_history: list[dict] = []
```

**Step 4: Modify engine.py run() to auto-fetch prices**

Add at the beginning of `run()` method:

```python
def run(self) -> None:
    """Execute the backtest simulation."""
    from lynx.backtest.costs import calculate_buy_cost
    from lynx.backtest.defaults import get_fees_for_symbol, get_lot_size_for_symbol

    # Auto-fetch prices if needed
    if self.price is None and self.auto_fetch_prices:
        from lynx.data.cache import fetch_prices_with_cache
        from lynx.data.exceptions import InvalidSymbolError
        from lynx.data.yahoo import validate_symbols

        # Get symbols from entry signal columns
        symbols = list(self.entry_signal.columns)

        # Validate symbols
        validation = validate_symbols(symbols)
        if validation.invalid_symbols:
            raise InvalidSymbolError(
                f"Cannot fetch from Yahoo Finance: {validation.invalid_symbols}"
            )

        # Get date range from signals
        start_date = min(
            self.entry_signal.index.min(),
            self.exit_signal.index.min(),
        )
        end_date = max(
            self.entry_signal.index.max(),
            self.exit_signal.index.max(),
        )

        # Convert to date if Timestamp
        if hasattr(start_date, 'date'):
            start_date = start_date.date()
        if hasattr(end_date, 'date'):
            end_date = end_date.date()

        # Fetch prices
        self.price = fetch_prices_with_cache(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
        )

    # Rest of existing run() code...
    symbols = list(self.price.columns)
    dates = self.price.index.tolist()
    # ... (keep all existing code)
```

**Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/unit/test_backtest_auto_fetch.py -v`
Expected: All tests PASS

**Step 6: Run all backtest tests to ensure no regression**

Run: `source .venv/bin/activate && pytest tests/unit/test_backtest*.py tests/integration/test_backtest.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/lynx/backtest/engine.py tests/unit/test_backtest_auto_fetch.py
git commit -m "feat(backtest): add auto_fetch_prices to BacktestEngine"
```

---

## Task 6: Update backtest() Function API

**Files:**
- Modify: `src/lynx/backtest/engine.py`
- Create: `tests/integration/test_backtest_auto_fetch.py`

**Step 1: Write integration test**

Create `tests/integration/test_backtest_auto_fetch.py`:

```python
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
        """Sample entry signal."""
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        return pd.DataFrame({"AAPL": [1, 0, 0, 0, 0]}, index=dates)

    @pytest.fixture
    def exit_signal(self):
        """Sample exit signal."""
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        return pd.DataFrame({"AAPL": [0, 0, 1, 0, 0]}, index=dates)

    @pytest.fixture
    def mock_prices(self):
        """Mock prices from Yahoo Finance."""
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        return pd.DataFrame(
            {"AAPL": [150.0, 151.0, 152.0, 153.0, 154.0]},
            index=dates,
        )

    @patch("lynx.backtest.engine.validate_symbols")
    @patch("lynx.backtest.engine.fetch_prices_with_cache")
    def test_backtest_without_price_parameter(
        self, mock_fetch, mock_validate, entry_signal, exit_signal, mock_prices
    ):
        """lynx.backtest() should work without price parameter."""
        mock_validate.return_value = ValidationResult(
            valid_symbols=["AAPL"],
            invalid_symbols=[],
        )
        mock_fetch.return_value = mock_prices

        run = lynx.backtest(
            strategy_name="test_auto_fetch",
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            # price not provided - should auto-fetch
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
```

**Step 2: Update backtest() function signature**

Modify the `backtest()` function in `src/lynx/backtest/engine.py`:

```python
def backtest(
    strategy_name: str,
    entry_signal: pd.DataFrame,
    exit_signal: pd.DataFrame,
    price: pd.DataFrame | None = None,  # Now optional
    initial_capital: float = 1_000_000,
    stop_loss: float | None = None,
    take_profit: float | None = None,
    conflict_mode: ConflictMode = "exit_first",
    fees: dict[str, dict[str, float]] | None = None,
    lot_size: dict[str, int] | None = None,
    auto_fetch_prices: bool = True,  # New parameter
) -> "Run":
    """Run a backtest and return a saved Run object.

    Args:
        strategy_name: Name for the strategy
        entry_signal: Entry signal DataFrame (0-1 values)
        exit_signal: Exit signal DataFrame (0-1 values)
        price: Close price DataFrame (optional if auto_fetch_prices=True)
        initial_capital: Starting capital (default: 1,000,000)
        stop_loss: Stop loss percentage (e.g., 0.05 for 5%)
        take_profit: Take profit percentage (e.g., 0.10 for 10%)
        conflict_mode: How to handle entry/exit conflicts
        fees: Custom fee configuration
        lot_size: Custom lot size configuration
        auto_fetch_prices: Auto-fetch prices from Yahoo Finance if not provided

    Returns:
        Run object with trades, metrics, and equity curve saved

    Raises:
        ValidationError: If inputs are invalid
        InvalidSymbolError: If auto-fetch is enabled and symbols are invalid
    """
    from lynx.backtest.validators import validate_backtest_inputs
    from lynx.run import Run
    from lynx.storage import sqlite

    # Validate inputs (only validate price if provided)
    if price is not None:
        validate_backtest_inputs(entry_signal, exit_signal, price)

    # Initialize database
    sqlite.init_db()

    # Run backtest
    engine = BacktestEngine(
        entry_signal=entry_signal,
        exit_signal=exit_signal,
        price=price,
        initial_capital=initial_capital,
        stop_loss=stop_loss,
        take_profit=take_profit,
        conflict_mode=conflict_mode,
        fees=fees,
        lot_size=lot_size,
        auto_fetch_prices=auto_fetch_prices,
    )
    engine.run()

    # Create trades DataFrame
    trades_df = pd.DataFrame(engine.trades)
    # ... rest of existing code
```

**Step 3: Run integration tests**

Run: `source .venv/bin/activate && pytest tests/integration/test_backtest_auto_fetch.py -v`
Expected: All tests PASS

**Step 4: Run full test suite**

Run: `source .venv/bin/activate && pytest`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/lynx/backtest/engine.py tests/integration/test_backtest_auto_fetch.py
git commit -m "feat(backtest): update backtest() API for optional price parameter"
```

---

## Task 7: Update Module Exports

**Files:**
- Modify: `src/lynx/__init__.py`
- Modify: `src/lynx/data/__init__.py`

**Step 1: Update lynx/data/__init__.py exports**

Ensure `src/lynx/data/__init__.py` exports validation result:

```python
"""Data fetching and caching module."""

from lynx.data.cache import fetch_prices_with_cache, get_cache_dir
from lynx.data.exceptions import DataFetchError, InvalidSymbolError
from lynx.data.yahoo import ValidationResult, fetch_adjusted_prices, validate_symbols

__all__ = [
    "fetch_adjusted_prices",
    "fetch_prices_with_cache",
    "get_cache_dir",
    "validate_symbols",
    "ValidationResult",
    "DataFetchError",
    "InvalidSymbolError",
]
```

**Step 2: Update lynx/__init__.py to export data exceptions**

Add to `src/lynx/__init__.py`:

```python
from lynx.data.exceptions import DataFetchError, InvalidSymbolError

# Update __all__ to include new exports
```

**Step 3: Run linting**

Run: `source .venv/bin/activate && ruff check src/lynx/`
Expected: No errors

**Step 4: Commit**

```bash
git add src/lynx/__init__.py src/lynx/data/__init__.py
git commit -m "feat: export data module exceptions in public API"
```

---

## Task 8: Final Integration Test with Real Yahoo Finance

**Files:**
- Create: `tests/integration/test_yahoo_integration.py`

**Step 1: Create real integration test (skipped by default)**

```python
"""Real integration tests with Yahoo Finance API.

These tests make actual network calls and are skipped by default.
Run with: pytest tests/integration/test_yahoo_integration.py --run-integration
"""

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def run_integration(request):
    """Skip unless --run-integration is passed."""
    if not request.config.getoption("--run-integration", default=False):
        pytest.skip("Skipping integration test (use --run-integration to run)")


def test_fetch_real_prices(run_integration):
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


def test_validate_real_symbols(run_integration):
    """Test validating real symbols."""
    from lynx.data.yahoo import validate_symbols

    result = validate_symbols(["AAPL", "INVALID_SYMBOL_XYZ"])

    assert "AAPL" in result.valid_symbols
    assert "INVALID_SYMBOL_XYZ" in result.invalid_symbols
```

**Step 2: Add pytest option for integration tests**

Add to `conftest.py`:

```python
def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that make network calls",
    )
```

**Step 3: Commit**

```bash
git add tests/integration/test_yahoo_integration.py tests/conftest.py
git commit -m "test: add real Yahoo Finance integration tests"
```

---

## Task 9: Run Full Test Suite and Lint

**Step 1: Run ruff check**

Run: `source .venv/bin/activate && ruff check src/lynx/`
Expected: No errors

**Step 2: Run ruff format**

Run: `source .venv/bin/activate && ruff format src/lynx/`
Expected: Files formatted

**Step 3: Run all tests**

Run: `source .venv/bin/activate && pytest`
Expected: All tests PASS

**Step 4: Final commit if any formatting changes**

```bash
git add -A
git commit -m "chore: apply ruff formatting" --allow-empty
```

---

## Summary

After completing all tasks, the backtest engine will:

1. Accept signals-only input (no price required)
2. Automatically fetch Adj Close from Yahoo Finance
3. Cache price data locally in `~/.lynx/cache/prices/`
4. Validate symbols before fetching
5. Maintain backward compatibility with provided prices
