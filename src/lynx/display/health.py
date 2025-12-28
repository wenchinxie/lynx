"""Health indicator calculations for metrics display."""

from dataclasses import dataclass
from typing import Any

from lynx.display.metrics_format import format_metric_value, get_metric_label

# Metric categories for dashboard tabs (FR-014)
METRIC_CATEGORIES: dict[str, list[str]] = {
    "backtest": [
        "startDate",
        "endDate",
        "version",
        "feeRatio",
        "taxRatio",
        "tradeAt",
        "market",
        "freq",
        "expired",
        "updateDate",
        "nextTradingDate",
        "currentRebalanceDate",
        "nextRebalanceDate",
        "livePerformanceStart",
        "stopLoss",
        "takeProfit",
        "trailStop",
    ],
    "profitability": [
        "annualReturn",
        "alpha",
        "beta",
        "avgNStock",
        "maxNStock",
    ],
    "risk": [
        "maxDrawdown",
        "avgDrawdown",
        "avgDrawdownDays",
        "valueAtRisk",
        "cvalueAtRisk",
    ],
    "ratio": [
        "sharpeRatio",
        "sortinoRatio",
        "calmarRatio",
        "volatility",
        "profitFactor",
        "tailRatio",
    ],
    "winrate": [
        "winRate",
        "m12WinRate",
        "expectancy",
        "mae",
        "mfe",
    ],
    "liquidity": [
        "capacity",
        "disposalStockRatio",
        "warningStockRatio",
        "fullDeliveryStockRatio",
        "buyHigh",
        "sellLow",
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
HEALTH_THRESHOLDS: dict[str, HealthThreshold] = {
    "sharpeRatio": HealthThreshold(green=1.0, yellow=0.5, higher_is_better=True),
    "sortinoRatio": HealthThreshold(green=1.5, yellow=0.75, higher_is_better=True),
    "calmarRatio": HealthThreshold(green=1.0, yellow=0.5, higher_is_better=True),
    "maxDrawdown": HealthThreshold(
        green=-0.15, yellow=-0.30, higher_is_better=True
    ),  # -15% is better than -30%
    "avgDrawdown": HealthThreshold(green=-0.05, yellow=-0.10, higher_is_better=True),
    "winRate": HealthThreshold(green=0.50, yellow=0.40, higher_is_better=True),
    "m12WinRate": HealthThreshold(green=0.50, yellow=0.40, higher_is_better=True),
    "annualReturn": HealthThreshold(green=0.15, yellow=0.05, higher_is_better=True),
    "profitFactor": HealthThreshold(green=1.5, yellow=1.0, higher_is_better=True),
    "volatility": HealthThreshold(
        green=0.15, yellow=0.25, higher_is_better=False
    ),  # Lower volatility is better
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

        for metric_key in METRIC_CATEGORIES.get(category, []):
            if metric_key not in metrics:
                continue

            value = metrics[metric_key]

            # Format the metric value
            formatted = format_metric_value(metric_key, value)

            # Calculate health status
            health = None
            if not formatted["is_special"] and isinstance(value, (int, float)):
                health = calculate_health_status(metric_key, value)

            # Update summary counts
            if health:
                summary[health] += 1

            category_metrics.append(
                {
                    "key": metric_key,
                    "label": get_metric_label(metric_key),
                    "raw": formatted["raw"],
                    "formatted": formatted["formatted"],
                    "health": health,
                    "is_negative": formatted["is_negative"],
                    "is_special": formatted["is_special"],
                }
            )

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
