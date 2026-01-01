"""Explain functionality for debugging why a stock was or wasn't selected."""

from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd

from lynx.exceptions import ValidationError

if TYPE_CHECKING:
    from lynx.run import Run


def explain_symbol(
    run: "Run",
    symbol: str | list[str],
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
) -> pd.DataFrame | dict[str, pd.DataFrame]:
    """Explain why a stock was or wasn't selected based on logged signals.

    Args:
        run: The Run object containing signal artifacts
        symbol: Stock symbol(s) to analyze
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        If single symbol: DataFrame with signal timeline
        If multiple symbols: Dict mapping symbol to DataFrame

    Raises:
        ValidationError: If no signals are logged
    """
    # Get all signal artifacts
    signals = _get_signal_artifacts(run)

    if not signals:
        raise ValidationError(
            "No signal artifacts logged. Use run.signal(name, df) to log signals before calling explain()."
        )

    # Handle multiple symbols
    if isinstance(symbol, list):
        return {s: _explain_single_symbol(signals, s, start_date, end_date) for s in symbol}

    return _explain_single_symbol(signals, symbol, start_date, end_date)


def _get_signal_artifacts(run: "Run") -> dict[str, pd.DataFrame]:
    """Get all signal-type artifacts from the run.

    Args:
        run: The Run object

    Returns:
        Dict mapping signal name to DataFrame
    """
    signals = {}

    # Check in-memory artifacts first
    for name, (artifact_type, df) in run._artifacts.items():
        if artifact_type == "signal":
            signals[name] = df

    return signals


def _explain_single_symbol(
    signals: dict[str, pd.DataFrame],
    symbol: str,
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
) -> pd.DataFrame:
    """Explain signal conditions for a single symbol.

    Args:
        signals: Dict of signal name to DataFrame
        symbol: Stock symbol to analyze
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        DataFrame with signal timeline for the symbol
    """
    # Build timeline DataFrame
    timeline_data = {}

    for signal_name, signal_df in signals.items():
        if symbol in signal_df.columns:
            timeline_data[signal_name] = signal_df[symbol]
        else:
            # Symbol not in this signal, fill with NaN
            timeline_data[signal_name] = pd.Series(
                [pd.NA] * len(signal_df), index=signal_df.index, name=signal_name
            )

    if not timeline_data:
        # No data found for symbol
        return pd.DataFrame({"message": [f"Symbol '{symbol}' not found in any signal"]})

    # Combine into single DataFrame
    result = pd.DataFrame(timeline_data)

    # Apply date filters
    if start_date is not None:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        result = result[result.index >= start_date]

    if end_date is not None:
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        result = result[result.index <= end_date]

    # Add summary column showing if all signals are True
    if len(result.columns) > 0 and result.columns[0] != "message":
        # For boolean signals, show combined status
        bool_cols = [col for col in result.columns if result[col].dtype == bool or result[col].dtype == "boolean"]
        if bool_cols:
            result["all_conditions_met"] = result[bool_cols].all(axis=1)

    return result
