"""Metric value formatting utilities for display."""

import math
from datetime import datetime
from typing import Any

# Metrics that should be displayed as percentages
# Support both camelCase and snake_case
PERCENTAGE_METRICS = {
    "annualReturn", "annual_return", "annualized_return",
    "total_return",
    "alpha",
    "beta",
    "maxDrawdown", "max_drawdown",
    "avgDrawdown", "avg_drawdown",
    "volatility",
    "winRate", "win_rate",
    "m12WinRate", "m12_win_rate",
    "feeRatio", "fee_ratio",
    "taxRatio", "tax_ratio",
    "disposalStockRatio", "disposal_stock_ratio",
    "warningStockRatio", "warning_stock_ratio",
    "fullDeliveryStockRatio", "full_delivery_stock_ratio",
    "valueAtRisk", "value_at_risk",
    "cvalueAtRisk", "cvalue_at_risk",
}

# Metrics that represent large numbers (capacity, etc.)
LARGE_NUMBER_METRICS = {
    "capacity",
}

# Metrics that should be formatted as ratios (2-4 decimal places)
RATIO_METRICS = {
    "sharpeRatio", "sharpe_ratio",
    "sortinoRatio", "sortino_ratio",
    "calmarRatio", "calmar_ratio",
    "profitFactor", "profit_factor",
    "tailRatio", "tail_ratio",
    "expectancy",
    "mae",
    "mfe",
}

# Metrics that should be formatted as integers
INTEGER_METRICS = {
    "avgNStock", "avg_n_stock",
    "maxNStock", "max_n_stock",
    "avgDrawdownDays", "avg_drawdown_days",
    "buyHigh", "buy_high",
    "sellLow", "sell_low",
    "num_trades",
}

# Metrics that should be formatted as floats with 1 decimal
FLOAT_1_METRICS = {
    "avg_trade_duration_days",
}

# Metrics that are Unix timestamps (should be converted to date strings)
TIMESTAMP_METRICS = {
    "startDate", "start_date",
    "endDate", "end_date",
    "updateDate", "update_date",
    "nextTradingDate", "next_trading_date",
    "currentRebalanceDate", "current_rebalance_date",
    "nextRebalanceDate", "next_rebalance_date",
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
    elif key in FLOAT_1_METRICS:
        formatted = f"{numeric_value:.1f}"
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
    # Special cases - support both camelCase and snake_case
    label_overrides = {
        # Annual Return (unify all variants to same label for deduplication)
        "annualReturn": "Annual Return",
        "annual_return": "Annual Return",
        "annualized_return": "Annual Return",
        "total_return": "Total Return",
        # Ratios
        "sharpeRatio": "Sharpe Ratio",
        "sharpe_ratio": "Sharpe Ratio",
        "sortinoRatio": "Sortino Ratio",
        "sortino_ratio": "Sortino Ratio",
        "calmarRatio": "Calmar Ratio",
        "calmar_ratio": "Calmar Ratio",
        "profitFactor": "Profit Factor",
        "profit_factor": "Profit Factor",
        "tailRatio": "Tail Ratio",
        "tail_ratio": "Tail Ratio",
        # Drawdown
        "maxDrawdown": "Max Drawdown",
        "max_drawdown": "Max Drawdown",
        "avgDrawdown": "Avg Drawdown",
        "avg_drawdown": "Avg Drawdown",
        "avgDrawdownDays": "Avg Drawdown Days",
        "avg_drawdown_days": "Avg Drawdown Days",
        # Risk
        "valueAtRisk": "Value at Risk",
        "value_at_risk": "Value at Risk",
        "cvalueAtRisk": "CVaR",
        "cvalue_at_risk": "CVaR",
        # Win Rate
        "winRate": "Win Rate",
        "win_rate": "Win Rate",
        "m12WinRate": "12M Win Rate",
        "m12_win_rate": "12M Win Rate",
        # Stock counts
        "avgNStock": "Avg # Stocks",
        "avg_n_stock": "Avg # Stocks",
        "maxNStock": "Max # Stocks",
        "max_n_stock": "Max # Stocks",
        # Fee/Tax
        "feeRatio": "Fee Ratio",
        "fee_ratio": "Fee Ratio",
        "taxRatio": "Tax Ratio",
        "tax_ratio": "Tax Ratio",
        # Dates
        "tradeAt": "Trade At",
        "trade_at": "Trade At",
        "startDate": "Start Date",
        "start_date": "Start Date",
        "endDate": "End Date",
        "end_date": "End Date",
        "updateDate": "Update Date",
        "update_date": "Update Date",
        "nextTradingDate": "Next Trading Date",
        "next_trading_date": "Next Trading Date",
        "currentRebalanceDate": "Current Rebalance",
        "current_rebalance_date": "Current Rebalance",
        "nextRebalanceDate": "Next Rebalance",
        "next_rebalance_date": "Next Rebalance",
        "livePerformanceStart": "Live Start",
        "live_performance_start": "Live Start",
        # Stock ratios
        "disposalStockRatio": "Disposal Stock %",
        "disposal_stock_ratio": "Disposal Stock %",
        "warningStockRatio": "Warning Stock %",
        "warning_stock_ratio": "Warning Stock %",
        "fullDeliveryStockRatio": "Full Delivery %",
        "full_delivery_stock_ratio": "Full Delivery %",
        # Trading
        "buyHigh": "Buy High",
        "buy_high": "Buy High",
        "sellLow": "Sell Low",
        "sell_low": "Sell Low",
        "stopLoss": "Stop Loss",
        "stop_loss": "Stop Loss",
        "takeProfit": "Take Profit",
        "take_profit": "Take Profit",
        "trailStop": "Trail Stop",
        "trail_stop": "Trail Stop",
        # Other
        "mae": "MAE",
        "mfe": "MFE",
        "num_trades": "# Trades",
        "avg_trade_duration_days": "Avg Trade Duration",
    }

    if key in label_overrides:
        return label_overrides[key]

    # Convert snake_case to Title Case
    if "_" in key:
        return " ".join(word.title() for word in key.split("_"))

    # Convert camelCase to Title Case
    result = []
    for i, char in enumerate(key):
        if char.isupper() and i > 0:
            result.append(" ")
        result.append(char)
    return "".join(result).title()
