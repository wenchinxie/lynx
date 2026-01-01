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
