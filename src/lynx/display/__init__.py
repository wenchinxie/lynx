"""Display module for stats, plots, comparisons, explain, time formatting, health indicators, and coverage analysis."""

from lynx.display.coverage import (
    CoverageAnalysis,
    calculate_coverage,
    calculate_portfolio_coverage,
    calculate_watchlist_coverage,
)
from lynx.display.explain import explain_symbol
from lynx.display.health import (
    CATEGORY_ORDER,
    DEFAULT_TAB,
    HEALTH_THRESHOLDS,
    METRIC_CATEGORIES,
    calculate_health_status,
    categorize_metrics,
    get_category_label,
)
from lynx.display.metrics_format import format_metric_value, get_metric_label
from lynx.display.plot import compare_equity_curves, create_equity_curve
from lynx.display.stats import compare_stats, format_stats
from lynx.display.time_format import format_relative_time

__all__ = [
    "format_stats",
    "compare_stats",
    "create_equity_curve",
    "compare_equity_curves",
    "explain_symbol",
    "format_relative_time",
    "format_metric_value",
    "get_metric_label",
    "METRIC_CATEGORIES",
    "CATEGORY_ORDER",
    "DEFAULT_TAB",
    "HEALTH_THRESHOLDS",
    "calculate_health_status",
    "categorize_metrics",
    "get_category_label",
    # Coverage analysis (T071)
    "CoverageAnalysis",
    "calculate_coverage",
    "calculate_watchlist_coverage",
    "calculate_portfolio_coverage",
]
