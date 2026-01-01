# Auto Fetch Adjusted Prices Design

**Date:** 2026-01-01
**Status:** Draft
**Author:** Claude & User

## Overview

This feature enables the backtest engine to automatically fetch backward-adjusted (後復權) prices from Yahoo Finance, eliminating the need for users to provide price data manually. Users only need to supply entry/exit signals.

## Goals

1. Simplify backtest API - users provide only signals, not prices
2. Automatically fetch Adj Close from Yahoo Finance
3. Cache price data locally for performance
4. Validate symbols before fetching

## Non-Goals

1. Forward-adjusted prices (前復權) - may be added in future
2. Multiple data sources - Yahoo Finance only for now
3. Real-time price fetching - historical data only

## API Design

### New Backtest API

```python
import lynx

result = lynx.backtest(
    signals=signals_df,           # Required: entry/exit signals
    initial_capital=1_000_000,    # Existing parameter
    market="TW",                  # Existing parameter

    # New parameters
    auto_fetch_prices=True,       # Default: auto-fetch prices
    prices=None,                  # Optional: user-provided prices (for backward compatibility)
)
```

### Backward Compatibility

- If `prices` is provided, use user-provided prices (existing behavior)
- If `prices=None` and `auto_fetch_prices=True`, fetch from Yahoo Finance

### Signals DataFrame Structure

```python
signals = pd.DataFrame({
    'date': ['2024-01-02', '2024-01-15', '2024-02-01', ...],
    'symbol': ['2330.TW', '2330.TW', '2330.TW', ...],
    'entry_signal': [1, 0, 0, ...],      # 1 = entry, 0 = no signal
    'exit_signal': [0, 0, 1, ...],       # 1 = exit, 0 = no signal
})
```

## Module Structure

```
src/lynx/
├── data/
│   ├── __init__.py
│   ├── yahoo.py          # Yahoo Finance API wrapper
│   └── cache.py          # Local cache management
├── backtest/
│   ├── engine.py         # Modified to integrate price fetching
│   └── ...
```

## Data Fetching Module

### Yahoo Finance Wrapper (`data/yahoo.py`)

```python
def fetch_adjusted_prices(
    symbols: list[str],
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """
    Fetch Adj Close prices from Yahoo Finance.

    Args:
        symbols: List of Yahoo Finance compatible symbols
        start_date: Start date for price data
        end_date: End date for price data

    Returns:
        DataFrame with columns: date, symbol, close (adjusted)

    Raises:
        DataFetchError: If Yahoo Finance API fails
    """
```

### Cache Manager (`data/cache.py`)

**Cache Location:** `~/.lynx/cache/prices/`

**File Format:** Parquet (one file per symbol, e.g., `2330.TW.parquet`)

**Cache Strategy:**
- If cache exists and covers requested date range → use cache
- If cache is incomplete → fetch only missing dates, merge and update cache

```python
def fetch_prices_with_cache(
    symbols: list[str],
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """
    Fetch prices with caching support.

    1. Check local cache for each symbol
    2. Identify missing date ranges
    3. Fetch only missing data from Yahoo Finance
    4. Merge and update cache
    5. Return complete price DataFrame
    """
```

## Symbol Validation

### Validation Function

```python
def validate_symbols(symbols: list[str]) -> ValidationResult:
    """
    Validate symbols are fetchable from Yahoo Finance.

    Returns:
        ValidationResult with:
            - valid_symbols: list[str]
            - invalid_symbols: list[str]
            - errors: dict[str, str]  # symbol -> error message
    """
```

### Validation Behavior

**Mandatory validation** - invalid symbols always raise an error:

```python
validation = validate_symbols(symbols)

if validation.invalid_symbols:
    raise InvalidSymbolError(
        f"Cannot fetch from Yahoo Finance: {validation.invalid_symbols}"
    )
```

## Backtest Engine Integration

### Modified `BacktestEngine.run()` Flow

```python
class BacktestEngine:
    def run(self) -> Run:
        # 1. Validate signals
        validate_signals(self.signals)

        # 2. Fetch prices (new step)
        if self.prices is None and self.auto_fetch_prices:
            symbols = self.signals['symbol'].unique().tolist()
            start_date = self.signals['date'].min()
            end_date = self.signals['date'].max()

            # 2a. Validate symbols (mandatory)
            validation = validate_symbols(symbols)
            if validation.invalid_symbols:
                raise InvalidSymbolError(
                    f"Cannot fetch: {validation.invalid_symbols}"
                )

            # 2b. Fetch with cache
            self.prices = fetch_prices_with_cache(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
            )

        # 3. Validate prices
        validate_prices(self.prices)

        # 4. Execute backtest (existing logic)
        ...
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| Yahoo API failure (network error) | Raise `DataFetchError`, abort backtest |
| Symbol not found on Yahoo Finance | Raise `InvalidSymbolError`, abort backtest |
| Cache read failure | Log warning, re-fetch from API |

## Market Support

| User Input | Market | Notes |
|------------|--------|-------|
| `2330.TW` | Taiwan Listed | Direct use |
| `6510.TWO` | Taiwan OTC | Direct use |
| `AAPL` | US Stock | No suffix |
| `9988.HK` | Hong Kong | Direct use |

**Note:** Symbol format must be Yahoo Finance compatible. No automatic conversion is performed.

## Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    # Existing dependencies...
    "yfinance>=0.2.0",    # Yahoo Finance API
]
```

## Future Considerations

1. **Forward-adjusted prices (前復權)** - Add `adjustment_mode` parameter
2. **Multiple data sources** - Support other APIs beyond Yahoo Finance
3. **Cache expiration** - Auto-refresh stale cache data
4. **Parallel fetching** - Fetch multiple symbols concurrently

## Implementation Tasks

1. Add `yfinance` dependency
2. Create `src/lynx/data/` module
3. Implement `yahoo.py` with `fetch_adjusted_prices()`
4. Implement `cache.py` with local Parquet caching
5. Add `validate_symbols()` function
6. Modify `BacktestEngine` to integrate price fetching
7. Update `lynx.backtest()` API with new parameters
8. Add unit tests for data module
9. Add integration tests for backtest with auto-fetch
10. Update documentation
