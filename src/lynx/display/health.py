"""Health indicator calculations for metrics display."""

from dataclasses import dataclass
from typing import Any

from lynx.display.metrics_format import format_metric_value, get_metric_label

# Metric categories for dashboard tabs (FR-014)
# Support both camelCase and snake_case for flexibility
METRIC_CATEGORIES: dict[str, list[str]] = {
    "backtest": [
        "startDate", "start_date",
        "endDate", "end_date",
        "version",
        "feeRatio", "fee_ratio",
        "taxRatio", "tax_ratio",
        "tradeAt", "trade_at",
        "market",
        "freq",
        "expired",
        "updateDate", "update_date",
        "nextTradingDate", "next_trading_date",
        "currentRebalanceDate", "current_rebalance_date",
        "nextRebalanceDate", "next_rebalance_date",
        "livePerformanceStart", "live_performance_start",
        "stopLoss", "stop_loss",
        "takeProfit", "take_profit",
        "trailStop", "trail_stop",
        "num_trades",
        "avg_trade_duration_days",
    ],
    "profitability": [
        "annualReturn", "annual_return", "annualized_return",
        "total_return",
        "alpha",
        "beta",
        "avgNStock", "avg_n_stock",
        "maxNStock", "max_n_stock",
    ],
    "risk": [
        "maxDrawdown", "max_drawdown",
        "avgDrawdown", "avg_drawdown",
        "avgDrawdownDays", "avg_drawdown_days",
        "valueAtRisk", "value_at_risk",
        "cvalueAtRisk", "cvalue_at_risk",
    ],
    "ratio": [
        "sharpeRatio", "sharpe_ratio",
        "sortinoRatio", "sortino_ratio",
        "calmarRatio", "calmar_ratio",
        "volatility",
        "profitFactor", "profit_factor",
        "tailRatio", "tail_ratio",
    ],
    "winrate": [
        "winRate", "win_rate",
        "m12WinRate", "m12_win_rate",
        "expectancy",
        "mae",
        "mfe",
    ],
    "liquidity": [
        "capacity",
        "disposalStockRatio", "disposal_stock_ratio",
        "warningStockRatio", "warning_stock_ratio",
        "fullDeliveryStockRatio", "full_delivery_stock_ratio",
        "buyHigh", "buy_high",
        "sellLow", "sell_low",
    ],
}

# Tab display order (FR-020: profitability is default)
CATEGORY_ORDER: list[str] = [
    "profitability",
    "risk",
    "ratio",
    "winrate",
    "liquidity",
    "backtest",
]

# Default tab (FR-020)
DEFAULT_TAB: str = "profitability"


@dataclass
class HealthThreshold:
    """Threshold configuration for health status calculation."""

    green: float
    yellow: float
    higher_is_better: bool = True


# Health thresholds for key metrics (FR-024 to FR-027)
# Support both camelCase and snake_case
_sharpe_threshold = HealthThreshold(green=1.0, yellow=0.5, higher_is_better=True)
_sortino_threshold = HealthThreshold(green=1.5, yellow=0.75, higher_is_better=True)
_calmar_threshold = HealthThreshold(green=1.0, yellow=0.5, higher_is_better=True)
_max_dd_threshold = HealthThreshold(green=-0.15, yellow=-0.30, higher_is_better=True)
_avg_dd_threshold = HealthThreshold(green=-0.05, yellow=-0.10, higher_is_better=True)
_win_rate_threshold = HealthThreshold(green=0.50, yellow=0.40, higher_is_better=True)
_annual_return_threshold = HealthThreshold(green=0.15, yellow=0.05, higher_is_better=True)
_profit_factor_threshold = HealthThreshold(green=1.5, yellow=1.0, higher_is_better=True)
_volatility_threshold = HealthThreshold(green=0.15, yellow=0.25, higher_is_better=False)

HEALTH_THRESHOLDS: dict[str, HealthThreshold] = {
    # Sharpe
    "sharpeRatio": _sharpe_threshold,
    "sharpe_ratio": _sharpe_threshold,
    # Sortino
    "sortinoRatio": _sortino_threshold,
    "sortino_ratio": _sortino_threshold,
    # Calmar
    "calmarRatio": _calmar_threshold,
    "calmar_ratio": _calmar_threshold,
    # Max Drawdown (-15% is better than -30%)
    "maxDrawdown": _max_dd_threshold,
    "max_drawdown": _max_dd_threshold,
    # Avg Drawdown
    "avgDrawdown": _avg_dd_threshold,
    "avg_drawdown": _avg_dd_threshold,
    # Win Rate
    "winRate": _win_rate_threshold,
    "win_rate": _win_rate_threshold,
    "m12WinRate": _win_rate_threshold,
    "m12_win_rate": _win_rate_threshold,
    # Annual Return
    "annualReturn": _annual_return_threshold,
    "annual_return": _annual_return_threshold,
    "annualized_return": _annual_return_threshold,
    "total_return": _annual_return_threshold,
    # Profit Factor
    "profitFactor": _profit_factor_threshold,
    "profit_factor": _profit_factor_threshold,
    # Volatility (lower is better)
    "volatility": _volatility_threshold,
}


def calculate_health_status(key: str, value: float | None) -> str | None:
    """Calculate health status for a metric.

    Args:
        key: Metric name
        value: Metric value

    Returns:
        "green" | "yellow" | "red" | None (if no threshold defined)
    """
    if value is None:
        return None

    if key not in HEALTH_THRESHOLDS:
        return None

    threshold = HEALTH_THRESHOLDS[key]

    if threshold.higher_is_better:
        # Higher is better (e.g., Sharpe ratio, win rate)
        if value >= threshold.green:
            return "green"
        elif value >= threshold.yellow:
            return "yellow"
        else:
            return "red"
    else:
        # Lower is better (e.g., volatility)
        if value <= threshold.green:
            return "green"
        elif value <= threshold.yellow:
            return "yellow"
        else:
            return "red"


def categorize_metrics(metrics: dict[str, Any]) -> dict[str, dict]:
    """Categorize and format metrics with health indicators.

    Args:
        metrics: Raw metrics dict from run

    Returns:
        Dict with category names as keys, each containing:
        - metrics: list of formatted metrics with health status, sorted with red first
        - summary: dict with counts {"green": N, "yellow": N, "red": N}

    Example:
        >>> metrics = {"annualReturn": 0.18, "sharpeRatio": 1.2, "maxDrawdown": -0.25}
        >>> result = categorize_metrics(metrics)
        >>> result["profitability"]["metrics"][0]["key"]
        'annualReturn'
        >>> result["profitability"]["summary"]
        {'green': 1, 'yellow': 0, 'red': 0}
    """
    result = {}

    for category in CATEGORY_ORDER:
        category_metrics = []
        summary = {"green": 0, "yellow": 0, "red": 0}
        # Track labels we've already added to avoid duplicates
        category_seen: dict[str, dict] = {}

        for metric_key in METRIC_CATEGORIES.get(category, []):
            # Get the label to deduplicate camelCase/snake_case variants
            label = get_metric_label(metric_key)

            # Check if metric exists
            value = metrics.get(metric_key)

            # If we've already seen this label, only update if we found actual data
            if label in category_seen:
                # If current value is None but we already have data, skip
                if value is None:
                    continue
                # If we have data now but the previous entry was None, update it
                prev_entry = category_seen[label]
                if prev_entry["raw"] is None and value is not None:
                    # Remove the old None entry and add the new one with data
                    category_metrics.remove(prev_entry)
                else:
                    # Already have data or both are None, skip
                    continue

            # Format the metric value (handles None)
            formatted = format_metric_value(metric_key, value)

            # Calculate health status
            health = None
            if not formatted["is_special"] and isinstance(value, (int, float)):
                health = calculate_health_status(metric_key, value)

            # Update summary counts
            if health:
                summary[health] += 1

            entry = {
                "key": metric_key,
                "label": label,
                "raw": formatted["raw"],
                "formatted": formatted["formatted"],
                "health": health,
                "is_negative": formatted["is_negative"],
                "is_special": formatted["is_special"],
            }
            category_seen[label] = entry
            category_metrics.append(entry)

        # Sort metrics: red first, then yellow, then green, then None
        health_order = {"red": 0, "yellow": 1, "green": 2, None: 3}
        category_metrics.sort(key=lambda m: health_order.get(m["health"], 3))

        result[category] = {
            "metrics": category_metrics,
            "summary": summary,
        }

    return result


def get_category_label(category: str) -> str:
    """Get human-readable label for a category.

    Args:
        category: Category key (e.g., "profitability", "risk")

    Returns:
        Human-readable label (e.g., "Profitability", "Risk")
    """
    labels = {
        "backtest": "Backtest",
        "profitability": "Profitability",
        "risk": "Risk",
        "ratio": "Ratio",
        "winrate": "Win Rate",
        "liquidity": "Liquidity",
    }
    return labels.get(category, category.title())
