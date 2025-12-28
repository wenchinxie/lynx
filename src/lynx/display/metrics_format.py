"""Metric value formatting utilities for display."""

import math
from datetime import datetime
from typing import Any

# Metrics that should be displayed as percentages
PERCENTAGE_METRICS = {
    "annualReturn",
    "alpha",
    "beta",
    "maxDrawdown",
    "avgDrawdown",
    "volatility",
    "winRate",
    "m12WinRate",
    "feeRatio",
    "taxRatio",
    "disposalStockRatio",
    "warningStockRatio",
    "fullDeliveryStockRatio",
    "valueAtRisk",
    "cvalueAtRisk",
}

# Metrics that represent large numbers (capacity, etc.)
LARGE_NUMBER_METRICS = {
    "capacity",
}

# Metrics that should be formatted as ratios (2-4 decimal places)
RATIO_METRICS = {
    "sharpeRatio",
    "sortinoRatio",
    "calmarRatio",
    "profitFactor",
    "tailRatio",
    "expectancy",
    "mae",
    "mfe",
}

# Metrics that should be formatted as integers
INTEGER_METRICS = {
    "avgNStock",
    "maxNStock",
    "avgDrawdownDays",
    "buyHigh",
    "sellLow",
}

# Metrics that are Unix timestamps (should be converted to date strings)
TIMESTAMP_METRICS = {
    "startDate",
    "endDate",
    "updateDate",
    "nextTradingDate",
    "currentRebalanceDate",
    "nextRebalanceDate",
}


def _format_large_number(value: float) -> str:
    """Format a large number with K/M/B suffixes.

    Args:
        value: The number to format

    Returns:
        Formatted string like "143.3M", "1.5B", "50.2K"
    """
    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000:.1f}B"
    elif abs_value >= 1_000_000:
        return f"{sign}{abs_value / 1_000_000:.1f}M"
    elif abs_value >= 1_000:
        return f"{sign}{abs_value / 1_000:.1f}K"
    else:
        return f"{sign}{abs_value:.1f}"


def _format_percentage(value: float) -> str:
    """Format a decimal value as percentage.

    Args:
        value: The decimal value (e.g., 0.18494)

    Returns:
        Formatted percentage string (e.g., "18.49%")
    """
    return f"{value * 100:.2f}%"


def _format_ratio(value: float) -> str:
    """Format a ratio value with 2 decimal places.

    Args:
        value: The ratio value

    Returns:
        Formatted ratio string (e.g., "1.85")
    """
    return f"{value:.2f}"


def _format_integer(value: float) -> str:
    """Format a value as integer.

    Args:
        value: The value to format

    Returns:
        Formatted integer string
    """
    return str(int(value))


def _format_timestamp(value: float) -> str:
    """Format a Unix timestamp as a date string.

    Args:
        value: Unix timestamp (seconds since 1970-01-01)

    Returns:
        Formatted date string (e.g., "2025-12-15")
    """
    try:
        dt = datetime.fromtimestamp(value)
        return dt.strftime("%Y-%m-%d")
    except (OSError, ValueError):
        return str(value)


def format_metric_value(key: str, value: Any) -> dict:
    """Format a metric value for display.

    Args:
        key: Metric name (e.g., "sharpeRatio", "annualReturn")
        value: Raw metric value

    Returns:
        Dict with keys:
        - formatted: str - Display string (e.g., "18.49%", "143.3M", "∞", "—")
        - raw: Any - Original value
        - is_negative: bool - True if value < 0
        - is_special: bool - True if inf, -inf, or None

    Examples:
        >>> format_metric_value("annualReturn", 0.18494)
        {"formatted": "18.49%", "raw": 0.18494, "is_negative": False, "is_special": False}
        >>> format_metric_value("capacity", 143319492)
        {"formatted": "143.3M", "raw": 143319492, "is_negative": False, "is_special": False}
        >>> format_metric_value("sharpeRatio", float("inf"))
        {"formatted": "∞", "raw": inf, "is_negative": False, "is_special": True}
        >>> format_metric_value("winRate", None)
        {"formatted": "—", "raw": None, "is_negative": False, "is_special": True}
    """
    # Handle None values
    if value is None:
        return {
            "formatted": "—",
            "raw": None,
            "is_negative": False,
            "is_special": True,
        }

    # Handle infinity values (including string "Infinity" from JSON)
    if value == "Infinity" or (isinstance(value, float) and math.isinf(value) and value > 0):
        return {
            "formatted": "∞",
            "raw": float("inf"),
            "is_negative": False,
            "is_special": True,
        }
    if value == "-Infinity" or (isinstance(value, float) and math.isinf(value) and value < 0):
        return {
            "formatted": "-∞",
            "raw": float("-inf"),
            "is_negative": True,
            "is_special": True,
        }
    if isinstance(value, float) and math.isnan(value):
        return {
            "formatted": "—",
            "raw": value,
            "is_negative": False,
            "is_special": True,
        }

    # Handle string values (dates, etc.) - pass through as-is
    if isinstance(value, str):
        return {
            "formatted": value,
            "raw": value,
            "is_negative": False,
            "is_special": False,
        }

    # Handle numeric values
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        # Non-numeric values - convert to string
        return {
            "formatted": str(value),
            "raw": value,
            "is_negative": False,
            "is_special": False,
        }

    is_negative = numeric_value < 0

    # Format based on metric type
    if key in TIMESTAMP_METRICS:
        formatted = _format_timestamp(numeric_value)
    elif key in PERCENTAGE_METRICS:
        formatted = _format_percentage(numeric_value)
    elif key in LARGE_NUMBER_METRICS:
        formatted = _format_large_number(numeric_value)
    elif key in RATIO_METRICS:
        formatted = _format_ratio(numeric_value)
    elif key in INTEGER_METRICS:
        formatted = _format_integer(numeric_value)
    else:
        # Default: use 2 decimal places for unknown metrics
        formatted = f"{numeric_value:.2f}"

    return {
        "formatted": formatted,
        "raw": value,
        "is_negative": is_negative,
        "is_special": False,
    }


def get_metric_label(key: str) -> str:
    """Convert a metric key to a human-readable label.

    Args:
        key: Metric key (e.g., "sharpeRatio", "annualReturn")

    Returns:
        Human-readable label (e.g., "Sharpe Ratio", "Annual Return")
    """
    # Special cases
    label_overrides = {
        "annualReturn": "Annual Return",
        "sharpeRatio": "Sharpe Ratio",
        "sortinoRatio": "Sortino Ratio",
        "calmarRatio": "Calmar Ratio",
        "maxDrawdown": "Max Drawdown",
        "avgDrawdown": "Avg Drawdown",
        "avgDrawdownDays": "Avg Drawdown Days",
        "valueAtRisk": "Value at Risk",
        "cvalueAtRisk": "CVaR",
        "profitFactor": "Profit Factor",
        "tailRatio": "Tail Ratio",
        "winRate": "Win Rate",
        "m12WinRate": "12M Win Rate",
        "avgNStock": "Avg # Stocks",
        "maxNStock": "Max # Stocks",
        "feeRatio": "Fee Ratio",
        "taxRatio": "Tax Ratio",
        "tradeAt": "Trade At",
        "startDate": "Start Date",
        "endDate": "End Date",
        "disposalStockRatio": "Disposal Stock %",
        "warningStockRatio": "Warning Stock %",
        "fullDeliveryStockRatio": "Full Delivery %",
        "buyHigh": "Buy High",
        "sellLow": "Sell Low",
        "mae": "MAE",
        "mfe": "MFE",
        # New backtest fields
        "updateDate": "Update Date",
        "nextTradingDate": "Next Trading Date",
        "currentRebalanceDate": "Current Rebalance",
        "nextRebalanceDate": "Next Rebalance",
        "livePerformanceStart": "Live Start",
        "stopLoss": "Stop Loss",
        "takeProfit": "Take Profit",
        "trailStop": "Trail Stop",
    }

    if key in label_overrides:
        return label_overrides[key]

    # Convert camelCase to Title Case
    result = []
    for i, char in enumerate(key):
        if char.isupper() and i > 0:
            result.append(" ")
        result.append(char)
    return "".join(result).title()
