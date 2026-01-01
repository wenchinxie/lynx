# Backtest Engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement `lynx.backtest()` function that runs vectorized backtests from entry/exit signal DataFrames.

**Architecture:** Create a new `backtest/` module with four files: `defaults.py` (configuration), `validators.py` (input validation), `costs.py` (fee calculation), and `engine.py` (core logic). The engine processes signals day-by-day, manages positions, and outputs a Run object compatible with existing lynx infrastructure.

**Tech Stack:** Python 3.13, pandas 2.0+, numpy, existing lynx Run/metrics/storage modules.

**Design Doc:** `docs/plans/2026-01-01-backtest-engine-design.md`

---

## Task 1: Create defaults.py with fee and lot size configurations

**Files:**
- Create: `src/lynx/backtest/__init__.py`
- Create: `src/lynx/backtest/defaults.py`
- Test: `tests/unit/test_backtest_defaults.py`

**Step 1: Create backtest package directory**

```bash
mkdir -p src/lynx/backtest
```

**Step 2: Write the failing test**

```python
# tests/unit/test_backtest_defaults.py
"""Tests for backtest default configurations."""

import pytest
from lynx.backtest.defaults import (
    DEFAULT_FEES,
    DEFAULT_LOT_SIZE,
    get_fees_for_symbol,
    get_lot_size_for_symbol,
)


class TestDefaultFees:
    def test_tw_fees_exist(self):
        assert ".TW" in DEFAULT_FEES
        tw_fees = DEFAULT_FEES[".TW"]
        assert tw_fees["commission_rate"] == 0.001425
        assert tw_fees["commission_discount"] == 0.6
        assert tw_fees["tax_buy"] == 0.0
        assert tw_fees["tax_sell"] == 0.003
        assert tw_fees["slippage"] == 0.001

    def test_us_fees_exist(self):
        assert ".US" in DEFAULT_FEES
        us_fees = DEFAULT_FEES[".US"]
        assert us_fees["commission_rate"] == 0.0
        assert us_fees["tax_sell"] == 0.0

    def test_default_fees_exist(self):
        assert "_default" in DEFAULT_FEES


class TestDefaultLotSize:
    def test_tw_lot_size(self):
        assert DEFAULT_LOT_SIZE[".TW"] == 1000

    def test_us_lot_size(self):
        assert DEFAULT_LOT_SIZE[".US"] == 1

    def test_default_lot_size(self):
        assert DEFAULT_LOT_SIZE["_default"] == 1


class TestGetFeesForSymbol:
    def test_tw_symbol(self):
        fees = get_fees_for_symbol("2330.TW")
        assert fees["commission_rate"] == 0.001425
        assert fees["tax_sell"] == 0.003

    def test_us_symbol(self):
        fees = get_fees_for_symbol("AAPL.US")
        assert fees["commission_rate"] == 0.0
        assert fees["tax_sell"] == 0.0

    def test_unknown_suffix_uses_default(self):
        fees = get_fees_for_symbol("ABC.UK")
        assert fees == DEFAULT_FEES["_default"]

    def test_no_suffix_uses_default(self):
        fees = get_fees_for_symbol("2330")
        assert fees == DEFAULT_FEES["_default"]

    def test_custom_fees_override(self):
        custom = {".TW": {"commission_discount": 0.28}}
        fees = get_fees_for_symbol("2330.TW", custom)
        assert fees["commission_discount"] == 0.28
        assert fees["commission_rate"] == 0.001425  # inherited from default


class TestGetLotSizeForSymbol:
    def test_tw_symbol(self):
        lot_size = get_lot_size_for_symbol("2330.TW")
        assert lot_size == 1000

    def test_us_symbol(self):
        lot_size = get_lot_size_for_symbol("AAPL.US")
        assert lot_size == 1

    def test_custom_lot_size(self):
        custom = {".TW": 500}
        lot_size = get_lot_size_for_symbol("2330.TW", custom)
        assert lot_size == 500
```

**Step 3: Run test to verify it fails**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_defaults.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'lynx.backtest'"

**Step 4: Write minimal implementation**

```python
# src/lynx/backtest/__init__.py
"""Backtest engine for lynx."""

from lynx.backtest.defaults import (
    DEFAULT_FEES,
    DEFAULT_LOT_SIZE,
    get_fees_for_symbol,
    get_lot_size_for_symbol,
)

__all__ = [
    "DEFAULT_FEES",
    "DEFAULT_LOT_SIZE",
    "get_fees_for_symbol",
    "get_lot_size_for_symbol",
]
```

```python
# src/lynx/backtest/defaults.py
"""Default configurations for backtest engine."""

from typing import Any

# Default fees by market suffix
DEFAULT_FEES: dict[str, dict[str, float]] = {
    ".TW": {
        "commission_rate": 0.001425,     # 0.1425%
        "commission_discount": 0.6,       # 60% discount
        "tax_buy": 0.0,
        "tax_sell": 0.003,                # 0.3%
        "slippage": 0.001,                # 0.1%
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

# Default lot sizes by market suffix
DEFAULT_LOT_SIZE: dict[str, int] = {
    ".TW": 1000,
    ".US": 1,
    "_default": 1,
}


def _get_suffix(symbol: str) -> str:
    """Extract market suffix from symbol (e.g., '.TW' from '2330.TW')."""
    if "." in symbol:
        return "." + symbol.split(".")[-1]
    return "_default"


def get_fees_for_symbol(
    symbol: str,
    custom_fees: dict[str, dict[str, float]] | None = None,
) -> dict[str, float]:
    """Get fee configuration for a symbol.

    Args:
        symbol: Stock symbol (e.g., '2330.TW')
        custom_fees: Optional custom fee overrides

    Returns:
        Dict with fee configuration
    """
    suffix = _get_suffix(symbol)

    # Start with default fees
    base_fees = DEFAULT_FEES.get(suffix, DEFAULT_FEES["_default"]).copy()

    # Apply custom overrides if provided
    if custom_fees:
        custom_for_suffix = custom_fees.get(suffix, {})
        base_fees.update(custom_for_suffix)

    return base_fees


def get_lot_size_for_symbol(
    symbol: str,
    custom_lot_size: dict[str, int] | None = None,
) -> int:
    """Get lot size for a symbol.

    Args:
        symbol: Stock symbol (e.g., '2330.TW')
        custom_lot_size: Optional custom lot size overrides

    Returns:
        Lot size as integer
    """
    suffix = _get_suffix(symbol)

    if custom_lot_size and suffix in custom_lot_size:
        return custom_lot_size[suffix]

    return DEFAULT_LOT_SIZE.get(suffix, DEFAULT_LOT_SIZE["_default"])
```

**Step 5: Run test to verify it passes**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_defaults.py -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/lynx/backtest/ tests/unit/test_backtest_defaults.py
git commit -m "feat(backtest): add default fees and lot size configurations"
```

---

## Task 2: Create validators.py for input validation

**Files:**
- Create: `src/lynx/backtest/validators.py`
- Test: `tests/unit/test_backtest_validators.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_backtest_validators.py
"""Tests for backtest input validation."""

import pandas as pd
import pytest
from lynx.backtest.validators import validate_backtest_inputs
from lynx.exceptions import ValidationError


@pytest.fixture
def valid_entry_signal():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame({
        "2330.TW": [0.5, 0.0, 0.3, 0.0, 0.0],
        "2317.TW": [0.5, 0.0, 0.7, 0.0, 0.0],
    }, index=dates)


@pytest.fixture
def valid_exit_signal():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame({
        "2330.TW": [0.0, 0.0, 0.0, 1.0, 0.0],
        "2317.TW": [0.0, 0.0, 0.0, 0.5, 0.0],
    }, index=dates)


@pytest.fixture
def valid_price():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame({
        "2330.TW": [580.0, 582.0, 585.0, 590.0, 588.0],
        "2317.TW": [112.0, 113.0, 114.0, 115.0, 114.5],
    }, index=dates)


class TestValidateBacktestInputs:
    def test_valid_inputs_pass(self, valid_entry_signal, valid_exit_signal, valid_price):
        # Should not raise
        validate_backtest_inputs(valid_entry_signal, valid_exit_signal, valid_price)

    def test_entry_signal_not_dataframe_raises(self, valid_exit_signal, valid_price):
        with pytest.raises(ValidationError, match="entry_signal must be a DataFrame"):
            validate_backtest_inputs([1, 2, 3], valid_exit_signal, valid_price)

    def test_exit_signal_not_dataframe_raises(self, valid_entry_signal, valid_price):
        with pytest.raises(ValidationError, match="exit_signal must be a DataFrame"):
            validate_backtest_inputs(valid_entry_signal, "not a df", valid_price)

    def test_price_not_dataframe_raises(self, valid_entry_signal, valid_exit_signal):
        with pytest.raises(ValidationError, match="price must be a DataFrame"):
            validate_backtest_inputs(valid_entry_signal, valid_exit_signal, None)

    def test_mismatched_columns_raises(self, valid_entry_signal, valid_exit_signal, valid_price):
        # Add extra column to entry_signal
        entry_with_extra = valid_entry_signal.copy()
        entry_with_extra["EXTRA"] = 0.0
        with pytest.raises(ValidationError, match="columns must match"):
            validate_backtest_inputs(entry_with_extra, valid_exit_signal, valid_price)

    def test_entry_signal_values_out_of_range_raises(self, valid_exit_signal, valid_price):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        bad_entry = pd.DataFrame({
            "2330.TW": [1.5, 0.0, 0.0, 0.0, 0.0],  # > 1.0
            "2317.TW": [0.0, 0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        with pytest.raises(ValidationError, match="entry_signal values must be between 0 and 1"):
            validate_backtest_inputs(bad_entry, valid_exit_signal, valid_price)

    def test_exit_signal_values_out_of_range_raises(self, valid_entry_signal, valid_price):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        bad_exit = pd.DataFrame({
            "2330.TW": [-0.1, 0.0, 0.0, 0.0, 0.0],  # < 0
            "2317.TW": [0.0, 0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        with pytest.raises(ValidationError, match="exit_signal values must be between 0 and 1"):
            validate_backtest_inputs(valid_entry_signal, bad_exit, valid_price)

    def test_price_with_negative_values_raises(self, valid_entry_signal, valid_exit_signal):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        bad_price = pd.DataFrame({
            "2330.TW": [580.0, -1.0, 585.0, 590.0, 588.0],
            "2317.TW": [112.0, 113.0, 114.0, 115.0, 114.5],
        }, index=dates)
        with pytest.raises(ValidationError, match="price values must be positive"):
            validate_backtest_inputs(valid_entry_signal, valid_exit_signal, bad_price)

    def test_empty_price_raises(self, valid_entry_signal, valid_exit_signal):
        empty_price = pd.DataFrame()
        with pytest.raises(ValidationError, match="price DataFrame cannot be empty"):
            validate_backtest_inputs(valid_entry_signal, valid_exit_signal, empty_price)
```

**Step 2: Run test to verify it fails**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_validators.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/lynx/backtest/validators.py
"""Input validation for backtest engine."""

import pandas as pd

from lynx.exceptions import ValidationError


def validate_backtest_inputs(
    entry_signal: pd.DataFrame,
    exit_signal: pd.DataFrame,
    price: pd.DataFrame,
) -> None:
    """Validate backtest input DataFrames.

    Args:
        entry_signal: Entry signal DataFrame (0-1 values)
        exit_signal: Exit signal DataFrame (0-1 values)
        price: Price DataFrame (close prices)

    Raises:
        ValidationError: If validation fails
    """
    # Check types
    if not isinstance(entry_signal, pd.DataFrame):
        raise ValidationError("entry_signal must be a DataFrame")
    if not isinstance(exit_signal, pd.DataFrame):
        raise ValidationError("exit_signal must be a DataFrame")
    if not isinstance(price, pd.DataFrame):
        raise ValidationError("price must be a DataFrame")

    # Check price is not empty
    if price.empty:
        raise ValidationError("price DataFrame cannot be empty")

    # Check columns match
    entry_cols = set(entry_signal.columns)
    exit_cols = set(exit_signal.columns)
    price_cols = set(price.columns)

    if entry_cols != exit_cols or entry_cols != price_cols:
        raise ValidationError(
            f"All DataFrames columns must match. "
            f"entry_signal: {sorted(entry_cols)}, "
            f"exit_signal: {sorted(exit_cols)}, "
            f"price: {sorted(price_cols)}"
        )

    # Check entry_signal values in [0, 1]
    if (entry_signal.values < 0).any() or (entry_signal.values > 1).any():
        raise ValidationError("entry_signal values must be between 0 and 1")

    # Check exit_signal values in [0, 1]
    if (exit_signal.values < 0).any() or (exit_signal.values > 1).any():
        raise ValidationError("exit_signal values must be between 0 and 1")

    # Check price values are positive
    if (price.values <= 0).any():
        raise ValidationError("price values must be positive")
```

**Step 4: Update __init__.py**

```python
# src/lynx/backtest/__init__.py (update)
"""Backtest engine for lynx."""

from lynx.backtest.defaults import (
    DEFAULT_FEES,
    DEFAULT_LOT_SIZE,
    get_fees_for_symbol,
    get_lot_size_for_symbol,
)
from lynx.backtest.validators import validate_backtest_inputs

__all__ = [
    "DEFAULT_FEES",
    "DEFAULT_LOT_SIZE",
    "get_fees_for_symbol",
    "get_lot_size_for_symbol",
    "validate_backtest_inputs",
]
```

**Step 5: Run test to verify it passes**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_validators.py -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/lynx/backtest/validators.py src/lynx/backtest/__init__.py tests/unit/test_backtest_validators.py
git commit -m "feat(backtest): add input validation for entry/exit signals and price"
```

---

## Task 3: Create costs.py for trading cost calculations

**Files:**
- Create: `src/lynx/backtest/costs.py`
- Test: `tests/unit/test_backtest_costs.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_backtest_costs.py
"""Tests for trading cost calculations."""

import pytest
from lynx.backtest.costs import calculate_buy_cost, calculate_sell_revenue


class TestCalculateBuyCost:
    def test_basic_buy_cost(self):
        # price=100, shares=1000, commission=0.1%, slippage=0.1%
        fees = {
            "commission_rate": 0.001,
            "commission_discount": 1.0,
            "slippage": 0.001,
        }
        cost = calculate_buy_cost(price=100.0, shares=1000, fees=fees)
        # 100 * 1000 * (1 + 0.001 + 0.001) = 100,200
        assert cost == pytest.approx(100200.0)

    def test_tw_buy_cost_with_discount(self):
        # Taiwan market with broker discount
        fees = {
            "commission_rate": 0.001425,
            "commission_discount": 0.6,
            "slippage": 0.001,
        }
        cost = calculate_buy_cost(price=580.0, shares=1000, fees=fees)
        # 580 * 1000 * (1 + 0.001425*0.6 + 0.001)
        # = 580000 * (1 + 0.000855 + 0.001)
        # = 580000 * 1.001855
        # = 581075.9
        expected = 580000 * (1 + 0.001425 * 0.6 + 0.001)
        assert cost == pytest.approx(expected)

    def test_zero_commission(self):
        fees = {
            "commission_rate": 0.0,
            "commission_discount": 1.0,
            "slippage": 0.001,
        }
        cost = calculate_buy_cost(price=100.0, shares=100, fees=fees)
        # 100 * 100 * (1 + 0 + 0.001) = 10010
        assert cost == pytest.approx(10010.0)


class TestCalculateSellRevenue:
    def test_basic_sell_revenue(self):
        fees = {
            "commission_rate": 0.001,
            "commission_discount": 1.0,
            "tax_sell": 0.0,
            "slippage": 0.001,
        }
        revenue = calculate_sell_revenue(price=100.0, shares=1000, fees=fees)
        # 100 * 1000 * (1 - 0.001 - 0 - 0.001) = 99800
        assert revenue == pytest.approx(99800.0)

    def test_tw_sell_revenue_with_tax(self):
        # Taiwan market with sell tax
        fees = {
            "commission_rate": 0.001425,
            "commission_discount": 0.6,
            "tax_sell": 0.003,
            "slippage": 0.001,
        }
        revenue = calculate_sell_revenue(price=600.0, shares=1000, fees=fees)
        # 600 * 1000 * (1 - 0.001425*0.6 - 0.003 - 0.001)
        # = 600000 * (1 - 0.000855 - 0.003 - 0.001)
        # = 600000 * 0.995145
        expected = 600000 * (1 - 0.001425 * 0.6 - 0.003 - 0.001)
        assert revenue == pytest.approx(expected)

    def test_us_sell_no_tax(self):
        fees = {
            "commission_rate": 0.0,
            "commission_discount": 1.0,
            "tax_sell": 0.0,
            "slippage": 0.001,
        }
        revenue = calculate_sell_revenue(price=150.0, shares=100, fees=fees)
        # 150 * 100 * (1 - 0 - 0 - 0.001) = 14985
        assert revenue == pytest.approx(14985.0)
```

**Step 2: Run test to verify it fails**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_costs.py -v
```

Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/lynx/backtest/costs.py
"""Trading cost calculations for backtest engine."""


def calculate_buy_cost(
    price: float,
    shares: int,
    fees: dict[str, float],
) -> float:
    """Calculate total cost to buy shares including fees.

    Args:
        price: Price per share
        shares: Number of shares to buy
        fees: Fee configuration dict

    Returns:
        Total cost including commission and slippage
    """
    commission_rate = fees.get("commission_rate", 0.0)
    commission_discount = fees.get("commission_discount", 1.0)
    slippage = fees.get("slippage", 0.0)

    effective_commission = commission_rate * commission_discount
    multiplier = 1 + effective_commission + slippage

    return price * shares * multiplier


def calculate_sell_revenue(
    price: float,
    shares: int,
    fees: dict[str, float],
) -> float:
    """Calculate net revenue from selling shares after fees.

    Args:
        price: Price per share
        shares: Number of shares to sell
        fees: Fee configuration dict

    Returns:
        Net revenue after commission, tax, and slippage
    """
    commission_rate = fees.get("commission_rate", 0.0)
    commission_discount = fees.get("commission_discount", 1.0)
    tax_sell = fees.get("tax_sell", 0.0)
    slippage = fees.get("slippage", 0.0)

    effective_commission = commission_rate * commission_discount
    multiplier = 1 - effective_commission - tax_sell - slippage

    return price * shares * multiplier
```

**Step 4: Update __init__.py**

```python
# src/lynx/backtest/__init__.py (update)
"""Backtest engine for lynx."""

from lynx.backtest.costs import calculate_buy_cost, calculate_sell_revenue
from lynx.backtest.defaults import (
    DEFAULT_FEES,
    DEFAULT_LOT_SIZE,
    get_fees_for_symbol,
    get_lot_size_for_symbol,
)
from lynx.backtest.validators import validate_backtest_inputs

__all__ = [
    "DEFAULT_FEES",
    "DEFAULT_LOT_SIZE",
    "get_fees_for_symbol",
    "get_lot_size_for_symbol",
    "validate_backtest_inputs",
    "calculate_buy_cost",
    "calculate_sell_revenue",
]
```

**Step 5: Run test to verify it passes**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_costs.py -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/lynx/backtest/costs.py src/lynx/backtest/__init__.py tests/unit/test_backtest_costs.py
git commit -m "feat(backtest): add buy cost and sell revenue calculations"
```

---

## Task 4: Create engine.py with core backtest logic - Part 1 (Position class)

**Files:**
- Create: `src/lynx/backtest/engine.py`
- Test: `tests/unit/test_backtest_engine.py`

**Step 1: Write the failing test for Position class**

```python
# tests/unit/test_backtest_engine.py
"""Tests for backtest engine."""

import pandas as pd
import pytest
from datetime import date


class TestPosition:
    def test_create_position(self):
        from lynx.backtest.engine import Position

        pos = Position(
            symbol="2330.TW",
            shares=1000,
            entry_price=580.0,
            entry_date=date(2024, 1, 2),
            entry_cost=581000.0,
        )
        assert pos.symbol == "2330.TW"
        assert pos.shares == 1000
        assert pos.entry_price == 580.0
        assert pos.entry_cost == 581000.0

    def test_position_current_value(self):
        from lynx.backtest.engine import Position

        pos = Position(
            symbol="2330.TW",
            shares=1000,
            entry_price=580.0,
            entry_date=date(2024, 1, 2),
            entry_cost=581000.0,
        )
        assert pos.current_value(600.0) == 600000.0

    def test_position_return_pct(self):
        from lynx.backtest.engine import Position

        pos = Position(
            symbol="2330.TW",
            shares=1000,
            entry_price=580.0,
            entry_date=date(2024, 1, 2),
            entry_cost=581000.0,
        )
        # (600 - 580) / 580 = 0.0345
        assert pos.return_pct(600.0) == pytest.approx(0.0345, rel=0.01)

    def test_position_partial_exit(self):
        from lynx.backtest.engine import Position

        pos = Position(
            symbol="2330.TW",
            shares=1000,
            entry_price=580.0,
            entry_date=date(2024, 1, 2),
            entry_cost=581000.0,
        )
        exited_shares = pos.reduce(500)
        assert exited_shares == 500
        assert pos.shares == 500

    def test_position_full_exit(self):
        from lynx.backtest.engine import Position

        pos = Position(
            symbol="2330.TW",
            shares=1000,
            entry_price=580.0,
            entry_date=date(2024, 1, 2),
            entry_cost=581000.0,
        )
        exited_shares = pos.reduce(1000)
        assert exited_shares == 1000
        assert pos.shares == 0
```

**Step 2: Run test to verify it fails**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_engine.py::TestPosition -v
```

Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/lynx/backtest/engine.py
"""Core backtest engine."""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import pandas as pd


@dataclass
class Position:
    """Represents an open position."""

    symbol: str
    shares: int
    entry_price: float
    entry_date: date
    entry_cost: float

    def current_value(self, current_price: float) -> float:
        """Calculate current market value of position."""
        return self.shares * current_price

    def return_pct(self, current_price: float) -> float:
        """Calculate return percentage based on entry price."""
        return (current_price - self.entry_price) / self.entry_price

    def reduce(self, shares_to_exit: int) -> int:
        """Reduce position by given shares. Returns actual shares exited."""
        actual_exit = min(shares_to_exit, self.shares)
        self.shares -= actual_exit
        return actual_exit
```

**Step 4: Run test to verify it passes**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_engine.py::TestPosition -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/lynx/backtest/engine.py tests/unit/test_backtest_engine.py
git commit -m "feat(backtest): add Position dataclass for tracking open positions"
```

---

## Task 5: Create engine.py - Part 2 (BacktestEngine class skeleton)

**Files:**
- Modify: `src/lynx/backtest/engine.py`
- Modify: `tests/unit/test_backtest_engine.py`

**Step 1: Add tests for BacktestEngine initialization**

```python
# tests/unit/test_backtest_engine.py (append to file)

class TestBacktestEngine:
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        entry_signal = pd.DataFrame({
            "2330.TW": [0.5, 0.0, 0.0, 0.0, 0.0],
            "2317.TW": [0.5, 0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "2330.TW": [0.0, 0.0, 0.0, 1.0, 0.0],
            "2317.TW": [0.0, 0.0, 0.0, 1.0, 0.0],
        }, index=dates)
        price = pd.DataFrame({
            "2330.TW": [580.0, 585.0, 590.0, 595.0, 600.0],
            "2317.TW": [112.0, 113.0, 114.0, 115.0, 116.0],
        }, index=dates)
        return entry_signal, exit_signal, price

    def test_engine_initialization(self, sample_data):
        from lynx.backtest.engine import BacktestEngine

        entry, exit_, price = sample_data
        engine = BacktestEngine(
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=1_000_000,
        )
        assert engine.initial_capital == 1_000_000
        assert engine.cash == 1_000_000
        assert len(engine.positions) == 0

    def test_engine_with_stop_loss(self, sample_data):
        from lynx.backtest.engine import BacktestEngine

        entry, exit_, price = sample_data
        engine = BacktestEngine(
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=1_000_000,
            stop_loss=0.05,
        )
        assert engine.stop_loss == 0.05

    def test_engine_with_take_profit(self, sample_data):
        from lynx.backtest.engine import BacktestEngine

        entry, exit_, price = sample_data
        engine = BacktestEngine(
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=1_000_000,
            take_profit=0.10,
        )
        assert engine.take_profit == 0.10
```

**Step 2: Run test to verify it fails**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_engine.py::TestBacktestEngine -v
```

Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/lynx/backtest/engine.py (add to existing file)

from typing import Literal

ConflictMode = Literal["exit_first", "entry_first", "ignore"]


class BacktestEngine:
    """Vectorized backtest engine."""

    def __init__(
        self,
        entry_signal: pd.DataFrame,
        exit_signal: pd.DataFrame,
        price: pd.DataFrame,
        initial_capital: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        conflict_mode: ConflictMode = "exit_first",
        fees: dict[str, dict[str, float]] | None = None,
        lot_size: dict[str, int] | None = None,
    ):
        """Initialize backtest engine.

        Args:
            entry_signal: Entry signal DataFrame (0-1 values)
            exit_signal: Exit signal DataFrame (0-1 values)
            price: Close price DataFrame
            initial_capital: Starting capital
            stop_loss: Stop loss percentage (e.g., 0.05 for 5%)
            take_profit: Take profit percentage (e.g., 0.10 for 10%)
            conflict_mode: How to handle entry/exit conflicts
            fees: Custom fee configuration
            lot_size: Custom lot size configuration
        """
        self.entry_signal = entry_signal
        self.exit_signal = exit_signal
        self.price = price
        self.initial_capital = initial_capital
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.conflict_mode = conflict_mode
        self.custom_fees = fees
        self.custom_lot_size = lot_size

        # State
        self.cash = initial_capital
        self.positions: dict[str, Position] = {}  # symbol -> Position
        self.trades: list[dict] = []
        self.equity_history: list[dict] = []
```

**Step 4: Run test to verify it passes**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_engine.py::TestBacktestEngine -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/lynx/backtest/engine.py tests/unit/test_backtest_engine.py
git commit -m "feat(backtest): add BacktestEngine class skeleton"
```

---

## Task 6: Implement BacktestEngine.run() - Core simulation loop

**Files:**
- Modify: `src/lynx/backtest/engine.py`
- Modify: `tests/unit/test_backtest_engine.py`

**Step 1: Add tests for run() method**

```python
# tests/unit/test_backtest_engine.py (append to TestBacktestEngine class)

    def test_engine_run_simple_trade(self, sample_data):
        from lynx.backtest.engine import BacktestEngine

        entry, exit_, price = sample_data
        engine = BacktestEngine(
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=1_000_000,
        )
        engine.run()

        # Should have executed trades
        assert len(engine.trades) > 0

        # Should have equity history for each day
        assert len(engine.equity_history) == 5

    def test_engine_generates_correct_trades(self):
        from lynx.backtest.engine import BacktestEngine

        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        entry_signal = pd.DataFrame({
            "TEST.US": [1.0, 0.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "TEST.US": [0.0, 0.0, 1.0],
        }, index=dates)
        price = pd.DataFrame({
            "TEST.US": [100.0, 110.0, 120.0],
        }, index=dates)

        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=price,
            initial_capital=10_000,
        )
        engine.run()

        assert len(engine.trades) == 1
        trade = engine.trades[0]
        assert trade["symbol"] == "TEST.US"
        assert trade["entry_price"] == 100.0
        assert trade["exit_price"] == 120.0
        assert trade["exit_reason"] == "signal"

    def test_engine_respects_lot_size(self):
        from lynx.backtest.engine import BacktestEngine

        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        entry_signal = pd.DataFrame({
            "2330.TW": [1.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "2330.TW": [0.0, 1.0],
        }, index=dates)
        price = pd.DataFrame({
            "2330.TW": [580.0, 600.0],
        }, index=dates)

        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=price,
            initial_capital=1_000_000,
        )
        engine.run()

        # TW stocks must be bought in lots of 1000
        trade = engine.trades[0]
        assert trade["shares"] % 1000 == 0

    def test_engine_stop_loss_triggers(self):
        from lynx.backtest.engine import BacktestEngine

        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        entry_signal = pd.DataFrame({
            "TEST.US": [1.0, 0.0, 0.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "TEST.US": [0.0, 0.0, 0.0, 0.0],  # No exit signal
        }, index=dates)
        price = pd.DataFrame({
            "TEST.US": [100.0, 95.0, 90.0, 85.0],  # Price drops 15%
        }, index=dates)

        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=price,
            initial_capital=10_000,
            stop_loss=0.10,  # 10% stop loss
        )
        engine.run()

        # Should have exited due to stop loss
        assert len(engine.trades) == 1
        assert engine.trades[0]["exit_reason"] == "stop_loss"

    def test_engine_take_profit_triggers(self):
        from lynx.backtest.engine import BacktestEngine

        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        entry_signal = pd.DataFrame({
            "TEST.US": [1.0, 0.0, 0.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "TEST.US": [0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        price = pd.DataFrame({
            "TEST.US": [100.0, 105.0, 112.0, 115.0],  # Price rises 15%
        }, index=dates)

        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=price,
            initial_capital=10_000,
            take_profit=0.10,  # 10% take profit
        )
        engine.run()

        assert len(engine.trades) == 1
        assert engine.trades[0]["exit_reason"] == "take_profit"
```

**Step 2: Run test to verify it fails**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_engine.py::TestBacktestEngine::test_engine_run_simple_trade -v
```

Expected: FAIL

**Step 3: Write implementation**

```python
# src/lynx/backtest/engine.py (add run() method to BacktestEngine class)

    def run(self) -> None:
        """Execute the backtest simulation."""
        from lynx.backtest.costs import calculate_buy_cost, calculate_sell_revenue
        from lynx.backtest.defaults import get_fees_for_symbol, get_lot_size_for_symbol

        symbols = list(self.price.columns)
        dates = self.price.index.tolist()

        # Align signals to price dates
        entry_aligned = self.entry_signal.reindex(dates).fillna(0)
        exit_aligned = self.exit_signal.reindex(dates).fillna(0)

        # Track positions marked for exit (for next day execution)
        pending_exits: dict[str, str] = {}  # symbol -> reason

        for i, current_date in enumerate(dates):
            current_prices = self.price.loc[current_date]

            # Step 1: Execute pending exits (from previous day's stop/take profit)
            for symbol, reason in list(pending_exits.items()):
                if symbol in self.positions:
                    self._execute_exit(
                        symbol=symbol,
                        exit_date=current_date,
                        price=current_prices[symbol],
                        exit_ratio=1.0,
                        reason=reason,
                    )
            pending_exits.clear()

            # Step 2: Check stop loss / take profit at current prices
            for symbol, pos in list(self.positions.items()):
                current_price = current_prices[symbol]
                return_pct = pos.return_pct(current_price)

                if self.stop_loss and return_pct <= -self.stop_loss:
                    pending_exits[symbol] = "stop_loss"
                elif self.take_profit and return_pct >= self.take_profit:
                    pending_exits[symbol] = "take_profit"

            # Step 3: Process exit signals
            for symbol in symbols:
                exit_value = exit_aligned.loc[current_date, symbol]
                if exit_value > 0 and symbol in self.positions:
                    # Check for conflict
                    entry_value = entry_aligned.loc[current_date, symbol]
                    if entry_value > 0:
                        if self.conflict_mode == "entry_first":
                            continue  # Skip exit
                        elif self.conflict_mode == "ignore":
                            continue  # Skip both (entry handled later)

                    self._execute_exit(
                        symbol=symbol,
                        exit_date=current_date,
                        price=current_prices[symbol],
                        exit_ratio=exit_value,
                        reason="signal",
                    )

            # Step 4: Process entry signals
            entry_row = entry_aligned.loc[current_date]
            row_sum = entry_row.sum()

            if row_sum > 0:
                # Cap investment at 100% of cash
                invest_ratio = min(row_sum, 1.0)
                investable = self.cash * invest_ratio

                for symbol in symbols:
                    signal_value = entry_row[symbol]
                    if signal_value <= 0:
                        continue

                    # Skip if already holding
                    if symbol in self.positions:
                        continue

                    # Check for conflict in ignore mode
                    exit_value = exit_aligned.loc[current_date, symbol]
                    if exit_value > 0 and self.conflict_mode == "ignore":
                        continue

                    # Calculate allocation
                    weight = signal_value / row_sum
                    allocation = investable * weight

                    # Get lot size and fees
                    lot_size = get_lot_size_for_symbol(symbol, self.custom_lot_size)
                    fees = get_fees_for_symbol(symbol, self.custom_fees)
                    price = current_prices[symbol]

                    # Calculate shares (rounded down to lot size)
                    max_shares = int(allocation / price)
                    shares = (max_shares // lot_size) * lot_size

                    if shares <= 0:
                        continue

                    # Calculate actual cost
                    cost = calculate_buy_cost(price, shares, fees)

                    if cost > self.cash:
                        continue

                    # Create position
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        shares=shares,
                        entry_price=price,
                        entry_date=current_date.date() if hasattr(current_date, 'date') else current_date,
                        entry_cost=cost,
                    )
                    self.cash -= cost

            # Step 5: Record daily equity
            holdings_value = sum(
                pos.current_value(current_prices[pos.symbol])
                for pos in self.positions.values()
            )
            equity = self.cash + holdings_value

            prev_equity = self.equity_history[-1]["equity"] if self.equity_history else self.initial_capital
            daily_return = (equity - prev_equity) / prev_equity if prev_equity > 0 else 0.0

            self.equity_history.append({
                "date": current_date,
                "equity": equity,
                "cash": self.cash,
                "holdings_value": holdings_value,
                "daily_return": daily_return,
            })

        # Close any remaining positions at last price
        last_date = dates[-1]
        last_prices = self.price.loc[last_date]
        for symbol in list(self.positions.keys()):
            self._execute_exit(
                symbol=symbol,
                exit_date=last_date,
                price=last_prices[symbol],
                exit_ratio=1.0,
                reason="end_of_data",
            )

    def _execute_exit(
        self,
        symbol: str,
        exit_date,
        price: float,
        exit_ratio: float,
        reason: str,
    ) -> None:
        """Execute an exit order."""
        from lynx.backtest.costs import calculate_sell_revenue
        from lynx.backtest.defaults import get_fees_for_symbol

        pos = self.positions.get(symbol)
        if pos is None:
            return

        fees = get_fees_for_symbol(symbol, self.custom_fees)

        # Calculate shares to exit
        shares_to_exit = int(pos.shares * exit_ratio)
        if shares_to_exit <= 0:
            return

        # Get lot size for rounding
        from lynx.backtest.defaults import get_lot_size_for_symbol
        lot_size = get_lot_size_for_symbol(symbol, self.custom_lot_size)

        # Round to lot size (for partial exits)
        if exit_ratio < 1.0:
            shares_to_exit = (shares_to_exit // lot_size) * lot_size
            if shares_to_exit <= 0:
                return

        actual_exited = pos.reduce(shares_to_exit)
        revenue = calculate_sell_revenue(price, actual_exited, fees)
        self.cash += revenue

        # Calculate return for this trade
        entry_cost_per_share = pos.entry_cost / (pos.shares + actual_exited)
        trade_cost = entry_cost_per_share * actual_exited
        trade_return = (revenue - trade_cost) / trade_cost

        # Record trade
        self.trades.append({
            "symbol": symbol,
            "entry_date": pos.entry_date,
            "exit_date": exit_date.date() if hasattr(exit_date, 'date') else exit_date,
            "entry_price": pos.entry_price,
            "exit_price": price,
            "shares": actual_exited,
            "return": trade_return,
            "exit_reason": reason,
        })

        # Remove position if fully exited
        if pos.shares <= 0:
            del self.positions[symbol]
```

**Step 4: Run tests to verify they pass**

```bash
source .venv/bin/activate && pytest tests/unit/test_backtest_engine.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/lynx/backtest/engine.py tests/unit/test_backtest_engine.py
git commit -m "feat(backtest): implement BacktestEngine.run() with full trading logic"
```

---

## Task 7: Add backtest() function and integrate with lynx API

**Files:**
- Modify: `src/lynx/backtest/__init__.py`
- Modify: `src/lynx/backtest/engine.py`
- Modify: `src/lynx/__init__.py`
- Test: `tests/integration/test_backtest.py`

**Step 1: Write the integration test**

```python
# tests/integration/test_backtest.py
"""Integration tests for lynx.backtest()."""

import pandas as pd
import pytest
import lynx


@pytest.fixture
def backtest_data():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    entry_signal = pd.DataFrame({
        "2330.TW": [0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
        "2317.TW": [0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
    }, index=dates)
    exit_signal = pd.DataFrame({
        "2330.TW": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        "2317.TW": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    }, index=dates)
    price = pd.DataFrame({
        "2330.TW": [580.0, 585.0, 590.0, 600.0, 595.0, 600.0, 605.0, 610.0, 615.0, 620.0],
        "2317.TW": [112.0, 113.0, 114.0, 116.0, 115.0, 116.0, 117.0, 118.0, 119.0, 120.0],
    }, index=dates)
    return entry_signal, exit_signal, price


class TestLynxBacktest:
    def test_backtest_returns_run_object(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        assert run is not None
        assert run.id is not None
        assert run.strategy_name == "test_strategy"

    def test_backtest_calculates_metrics(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        assert "total_return" in run.metrics
        assert "sharpe_ratio" in run.metrics
        assert "max_drawdown" in run.metrics
        assert "num_trades" in run.metrics

    def test_backtest_saves_trades(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        trades = run.get_trades()
        assert len(trades) > 0
        assert "symbol" in trades.columns
        assert "entry_price" in trades.columns
        assert "exit_price" in trades.columns
        assert "shares" in trades.columns

    def test_backtest_saves_equity_curve(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        equity = run.get_data("equity")
        assert len(equity) == 10  # 10 trading days
        assert "equity" in equity.columns
        assert "cash" in equity.columns

    def test_backtest_can_be_loaded(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        # Load from storage
        loaded_run = lynx.load(run.id)
        assert loaded_run.id == run.id
        assert loaded_run.metrics["num_trades"] == run.metrics["num_trades"]

    def test_backtest_with_stop_loss(self, temp_data_dir):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        entry_signal = pd.DataFrame({
            "TEST.US": [1.0, 0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "TEST.US": [0.0, 0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        price = pd.DataFrame({
            "TEST.US": [100.0, 95.0, 88.0, 85.0, 80.0],
        }, index=dates)

        run = lynx.backtest(
            strategy_name="stop_loss_test",
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=price,
            initial_capital=10_000,
            stop_loss=0.10,
        )

        trades = run.get_trades()
        assert len(trades) == 1
        assert trades.iloc[0]["exit_reason"] == "stop_loss"

    def test_backtest_appears_in_runs_list(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="list_test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        runs_list = lynx.runs(strategy="list_test_strategy")
        assert len(runs_list) == 1
        assert runs_list[0].id == run.id
```

**Step 2: Run test to verify it fails**

```bash
source .venv/bin/activate && pytest tests/integration/test_backtest.py -v
```

Expected: FAIL

**Step 3: Add backtest function to engine.py**

```python
# src/lynx/backtest/engine.py (add at the end of file)

def backtest(
    strategy_name: str,
    entry_signal: pd.DataFrame,
    exit_signal: pd.DataFrame,
    price: pd.DataFrame,
    initial_capital: float,
    stop_loss: float | None = None,
    take_profit: float | None = None,
    conflict_mode: ConflictMode = "exit_first",
    fees: dict[str, dict[str, float]] | None = None,
    lot_size: dict[str, int] | None = None,
) -> "Run":
    """Run a backtest and return a saved Run object.

    Args:
        strategy_name: Name for the strategy
        entry_signal: Entry signal DataFrame (0-1 values)
        exit_signal: Exit signal DataFrame (0-1 values)
        price: Close price DataFrame
        initial_capital: Starting capital
        stop_loss: Stop loss percentage (e.g., 0.05 for 5%)
        take_profit: Take profit percentage (e.g., 0.10 for 10%)
        conflict_mode: How to handle entry/exit conflicts
        fees: Custom fee configuration
        lot_size: Custom lot size configuration

    Returns:
        Run object with trades, metrics, and equity curve saved

    Raises:
        ValidationError: If inputs are invalid
    """
    from lynx.backtest.validators import validate_backtest_inputs
    from lynx.run import Run
    from lynx.storage import sqlite

    # Validate inputs
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
    )
    engine.run()

    # Create trades DataFrame
    trades_df = pd.DataFrame(engine.trades)

    # Handle empty trades case
    if trades_df.empty:
        trades_df = pd.DataFrame({
            "symbol": pd.Series([], dtype=str),
            "entry_date": pd.Series([], dtype="datetime64[ns]"),
            "exit_date": pd.Series([], dtype="datetime64[ns]"),
            "entry_price": pd.Series([], dtype=float),
            "exit_price": pd.Series([], dtype=float),
            "shares": pd.Series([], dtype=int),
            "return": pd.Series([], dtype=float),
            "exit_reason": pd.Series([], dtype=str),
        })
    else:
        # Convert dates to datetime
        trades_df["entry_date"] = pd.to_datetime(trades_df["entry_date"])
        trades_df["exit_date"] = pd.to_datetime(trades_df["exit_date"])

    # Create equity DataFrame
    equity_df = pd.DataFrame(engine.equity_history)
    if not equity_df.empty:
        equity_df = equity_df.set_index("date")

    # Build params dict
    params = {
        "initial_capital": initial_capital,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "conflict_mode": conflict_mode,
    }

    # Create and save Run
    run = Run(name=strategy_name, params=params)
    run.trades(trades_df)
    run.data("equity", equity_df)
    run.signal("entry_signal", entry_signal)
    run.signal("exit_signal", exit_signal)
    run.data("price", price)
    run.save()

    return run
```

**Step 4: Update backtest/__init__.py**

```python
# src/lynx/backtest/__init__.py (replace entire file)
"""Backtest engine for lynx."""

from lynx.backtest.costs import calculate_buy_cost, calculate_sell_revenue
from lynx.backtest.defaults import (
    DEFAULT_FEES,
    DEFAULT_LOT_SIZE,
    get_fees_for_symbol,
    get_lot_size_for_symbol,
)
from lynx.backtest.engine import BacktestEngine, Position, backtest
from lynx.backtest.validators import validate_backtest_inputs

__all__ = [
    "DEFAULT_FEES",
    "DEFAULT_LOT_SIZE",
    "get_fees_for_symbol",
    "get_lot_size_for_symbol",
    "validate_backtest_inputs",
    "calculate_buy_cost",
    "calculate_sell_revenue",
    "BacktestEngine",
    "Position",
    "backtest",
]
```

**Step 5: Update main lynx/__init__.py**

```python
# src/lynx/__init__.py (add import and update __all__)

# At the top, add:
from lynx.backtest import backtest

# Update __all__ to include "backtest":
__all__ = [
    "log", "runs", "load", "delete", "dashboard", "config",
    "runs_today", "runs_last_7_days", "runs_last_30_days",
    "Run", "RunSummary",
    "get_watchlist", "set_watchlist", "add_to_watchlist", "remove_from_watchlist",
    "get_portfolio", "set_portfolio",
    "backtest",  # Add this
]
```

**Step 6: Run tests to verify they pass**

```bash
source .venv/bin/activate && pytest tests/integration/test_backtest.py -v
```

Expected: All tests PASS

**Step 7: Run all tests to ensure no regressions**

```bash
source .venv/bin/activate && pytest tests/ -v
```

Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lynx/backtest/ src/lynx/__init__.py tests/integration/test_backtest.py
git commit -m "feat(backtest): add lynx.backtest() function with full integration"
```

---

## Task 8: Add backtest fixtures to conftest.py

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Add backtest fixtures**

```python
# tests/conftest.py (append to existing file)

@pytest.fixture
def sample_entry_signal():
    """Create a sample entry signal DataFrame for backtesting."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "2330.TW": [0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
        "2317.TW": [0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
    }, index=dates)


@pytest.fixture
def sample_exit_signal():
    """Create a sample exit signal DataFrame for backtesting."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "2330.TW": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        "2317.TW": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    }, index=dates)


@pytest.fixture
def sample_backtest_price():
    """Create a sample price DataFrame for backtesting."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame({
        "2330.TW": [580.0, 585.0, 590.0, 600.0, 595.0, 600.0, 605.0, 610.0, 615.0, 620.0],
        "2317.TW": [112.0, 113.0, 114.0, 116.0, 115.0, 116.0, 117.0, 118.0, 119.0, 120.0],
    }, index=dates)
```

**Step 2: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add backtest fixtures to conftest.py"
```

---

## Task 9: Final verification and documentation

**Files:**
- None (verification only)

**Step 1: Run full test suite**

```bash
source .venv/bin/activate && pytest tests/ -v --tb=short
```

Expected: All tests PASS

**Step 2: Run type checking (if mypy is available)**

```bash
source .venv/bin/activate && python -m mypy src/lynx/backtest/ --ignore-missing-imports
```

Expected: No errors

**Step 3: Run linting**

```bash
source .venv/bin/activate && ruff check src/lynx/backtest/
```

Expected: No errors (or fix any issues)

**Step 4: Create final commit**

```bash
git add -A
git commit -m "chore: finalize backtest engine implementation"
```

**Step 5: Push branch**

```bash
git push -u origin feature/backtest-implementation
```

---

## Summary

After completing all tasks, the following files will be created/modified:

**New Files:**
- `src/lynx/backtest/__init__.py` - Module exports
- `src/lynx/backtest/defaults.py` - Default fees and lot sizes
- `src/lynx/backtest/validators.py` - Input validation
- `src/lynx/backtest/costs.py` - Trading cost calculations
- `src/lynx/backtest/engine.py` - Core backtest engine + backtest() function
- `tests/unit/test_backtest_defaults.py`
- `tests/unit/test_backtest_validators.py`
- `tests/unit/test_backtest_costs.py`
- `tests/unit/test_backtest_engine.py`
- `tests/integration/test_backtest.py`

**Modified Files:**
- `src/lynx/__init__.py` - Add backtest to public API
- `tests/conftest.py` - Add backtest fixtures
