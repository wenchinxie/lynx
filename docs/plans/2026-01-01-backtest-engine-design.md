# Lynx Backtest Engine Design

**Date:** 2026-01-01
**Status:** Approved
**Branch:** feature/backtest-implementation

## Overview

Lynx Backtest Engine is a vectorized backtesting engine that allows users to run strategy backtests using entry/exit signal DataFrames. The design goal is simplicity and seamless integration with the existing Lynx Run system.

## API Design

### Main Function

```python
import lynx
import pandas as pd

run = lynx.backtest(
    strategy_name="my_strategy",
    entry_signal=entry_df,      # DataFrame: index=date, columns=symbols, values=0-1
    exit_signal=exit_df,        # DataFrame: index=date, columns=symbols, values=0-1
    price=price_df,             # DataFrame: index=date, columns=symbols, values=close price
    initial_capital=1_000_000,

    # Optional parameters
    stop_loss=0.05,             # Stop loss 5% (None=disabled)
    take_profit=0.10,           # Take profit 10% (None=disabled)
    conflict_mode="exit_first", # entry/exit conflict: exit_first | entry_first | ignore
    fees=None,                  # Custom fees dict (None=use defaults)
    lot_size=None,              # Custom lot size dict (None=use defaults)
)

# Results are automatically saved to ~/.lynx/
run.stats()   # View performance metrics
run.plot()    # Plot equity curve
```

## Data Format

### Entry Signal DataFrame

```python
# entry_signal: 0-1 float, representing relative weight for each stock
             2330.TW  2317.TW  2454.TW
Date
2024-01-02      0.0      0.3      0.7    # 2317: 30%, 2454: 70%
2024-01-03      0.5      0.5      0.0    # 2330: 50%, 2317: 50%
2024-01-04      0.0      0.0      0.0    # No entry signal
```

**Weight Calculation:**
- Stock weight = stock value / daily row sum
- Investment ratio = daily row sum (if sum=0.8, invest 80% of available capital)

### Exit Signal DataFrame

```python
# exit_signal: 0-1 float, representing exit proportion
             2330.TW  2317.TW  2454.TW
Date
2024-01-05      0.0      1.0      0.5    # 2317: full exit, 2454: exit half
```

- `1.0` = Full exit
- `0.5` = Sell 50% of holdings
- `0.0` = No action

### Price DataFrame

```python
# price: Close prices
             2330.TW  2317.TW  2454.TW
Date
2024-01-02     580.0    112.0    890.0
2024-01-03     575.0    115.0    885.0
```

### Validation Rules

- All three DataFrames must have **identical columns** (raise error otherwise)
- Dates are based on price DataFrame; missing signals treated as 0
- Signals with no corresponding price are skipped

## Trading Costs and Units

### Default Fees (by stock symbol suffix)

```python
DEFAULT_FEES = {
    ".TW": {
        "commission_rate": 0.001425,     # Commission 0.1425%
        "commission_discount": 0.6,       # Broker discount 60%
        "tax_buy": 0.0,                   # No tax on buy
        "tax_sell": 0.003,                # Sell tax 0.3%
        "slippage": 0.001,                # Slippage 0.1%
    },
    ".US": {
        "commission_rate": 0.0,
        "commission_discount": 1.0,
        "tax_buy": 0.0,
        "tax_sell": 0.0,
        "slippage": 0.001,
    },
    "_default": {
        "commission_rate": 0.001,
        "commission_discount": 1.0,
        "tax_buy": 0.0,
        "tax_sell": 0.0,
        "slippage": 0.001,
    },
}
```

### Default Lot Sizes

```python
DEFAULT_LOT_SIZE = {
    ".TW": 1000,    # Taiwan stocks: 1 lot = 1000 shares
    ".US": 1,       # US stocks: can buy 1 share
    "_default": 1,
}
```

### Cost Calculation Formula

```python
# Buy cost
buy_cost = price * shares * (1 + commission_rate * commission_discount + slippage)

# Sell revenue
sell_revenue = price * shares * (1 - commission_rate * commission_discount - tax_sell - slippage)
```

### Custom Fees

```python
run = lynx.backtest(
    ...,
    fees={
        ".TW": {"commission_discount": 0.28},  # Override specific fields only
    },
)
```

## Trading Logic

### Daily Processing Flow

```
For each trading day (based on price dates):
1. Check stop loss / take profit → Mark positions for exit
2. Process exit_signal → Execute partial/full exits
3. Process entry_signal → Calculate buyable shares, create new positions
4. Record daily equity
```

### Conflict Handling (same day, same stock has both entry + exit)

```python
conflict_mode = "exit_first"  # Default

# exit_first: Exit first, then entry (exit takes priority)
# entry_first: Ignore exit, execute entry
# ignore: Execute neither
```

### Position Management Rules

- **One position per stock maximum** (no pyramiding)
- When already holding, new entry_signal is ignored
- After partial exit, remaining position continues as independent position

### Stop Loss / Take Profit Logic

```python
# Check at end of each day
for position in holdings:
    return_pct = (current_price - entry_price) / entry_price

    if stop_loss and return_pct <= -stop_loss:
        mark_for_exit(position, reason="stop_loss")

    if take_profit and return_pct >= take_profit:
        mark_for_exit(position, reason="take_profit")

# Marked positions exit next day at close price
```

### Capital Allocation

```python
# Daily investable capital = available cash * row_sum (row_sum capped at 1.0)
# Per-stock allocation = investable capital * (stock value / row_sum)
# Buyable shares = floor(allocated amount / price / lot_size) * lot_size
```

## Output and Integration

### Output Structure

`lynx.backtest()` returns a `Run` object containing:

```python
run = lynx.backtest(...)

# Auto-generated artifacts
run.get_trades()         # Trades DataFrame
run.get_data("equity")   # Daily equity curve DataFrame
run.get_data("holdings") # Daily holdings DataFrame

# Auto-calculated metrics (existing metrics.py)
run.metrics
# {
#     "total_return": 0.156,
#     "annualized_return": 0.089,
#     "sharpe_ratio": 1.23,
#     "max_drawdown": -0.082,
#     "win_rate": 0.58,
#     "profit_factor": 1.67,
#     "num_trades": 142,
#     "avg_trade_duration": 12.5,
# }
```

### Trades DataFrame Format

Compatible with existing lynx format:

```python
trades = run.get_trades()
#        symbol  entry_date  exit_date  entry_price  exit_price  shares  return  exit_reason
# 0    2330.TW  2024-01-02 2024-01-15        580.0       612.0    1000   0.055       signal
# 1    2317.TW  2024-01-02 2024-01-10        112.0       106.4    2000  -0.050    stop_loss
```

New columns:
- `shares`: Number of shares traded
- `exit_reason`: signal / stop_loss / take_profit

### Equity DataFrame Format

```python
equity = run.get_data("equity")
#              equity      cash  holdings_value  daily_return
# Date
# 2024-01-02  1000000   420000          580000           0.0
# 2024-01-03  1012350   420000          592350         0.012
```

### Existing Features Automatically Available

```python
run.stats()     # Display performance table
run.plot()      # Interactive equity curve
run.compare(other_run)  # Compare two backtests
```

## File Structure

### New Files

```
src/lynx/
├── __init__.py              # Add backtest() to public API
├── backtest/
│   ├── __init__.py          # Export backtest function
│   ├── engine.py            # Core backtest engine
│   ├── costs.py             # Fee and trading cost calculation
│   ├── validators.py        # Data validation
│   └── defaults.py          # Default fees, lot sizes
└── ...
```

### Module Responsibilities

| File | Responsibility |
|------|----------------|
| `engine.py` | Main backtest logic: signal processing, position management, daily simulation |
| `costs.py` | Trading cost calculation: commission, tax, slippage |
| `validators.py` | Input validation: DataFrame format, column consistency check |
| `defaults.py` | Default configuration: DEFAULT_FEES, DEFAULT_LOT_SIZE |

### Relationship with Existing Modules

```
backtest/engine.py
    ├── uses → run.py (Run class)
    ├── uses → metrics.py (calculate performance metrics)
    ├── uses → storage/ (auto-save)
    └── uses → exceptions.py (ValidationError)
```

### Public API Changes

```python
# src/lynx/__init__.py additions
from lynx.backtest import backtest

__all__ = [
    # existing...
    "backtest",  # new
]
```

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Signal format | 0-1 float | Allows weighted allocation |
| Conflict handling | Configurable, default exit_first | Flexibility with sensible default |
| Position management | One position per stock | Simplicity for v1 |
| Price data | Close price only | Simplicity for v1 |
| Capital allocation | Proportional to row sum | Intuitive cash management |
| Exit signal | 0-1 float | Support partial exits |
| Trading costs | Configurable by suffix | Multi-market support |
| Lot size | Configurable by suffix | Taiwan/US market compatibility |
| Missing data | Skip signal | Robust handling |
| Date alignment | Based on price | Clear reference point |
| Column alignment | Strict match required | Prevent silent errors |
| Auto-save | Yes | Seamless integration |
| Stop loss/take profit | Close price check | v1 simplicity |

## Future Enhancements (Not in v1)

- Pyramiding / position accumulation
- Intraday stop loss / take profit
- Cash interest calculation
- Dividend reinvestment
- Multi-currency support
- OHLC price execution options
