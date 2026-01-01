"""Statistics display formatting for Jupyter notebooks."""

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from lynx.run import Run


def format_stats(metrics: dict):
    """Format metrics as a styled pandas DataFrame for Jupyter display.

    Args:
        metrics: Dictionary of metric name -> value pairs

    Returns:
        Styled pandas DataFrame (Styler object)
    """
    # Create DataFrame with metric names and values
    df = pd.DataFrame([
        {"Metric": "Total Return", "Value": metrics.get("total_return", 0.0)},
        {"Metric": "Annualized Return", "Value": metrics.get("annualized_return", 0.0)},
        {"Metric": "Sharpe Ratio", "Value": metrics.get("sharpe_ratio", 0.0)},
        {"Metric": "Max Drawdown", "Value": metrics.get("max_drawdown", 0.0)},
        {"Metric": "Win Rate", "Value": metrics.get("win_rate", 0.0)},
        {"Metric": "Profit Factor", "Value": metrics.get("profit_factor", 0.0)},
        {"Metric": "Number of Trades", "Value": metrics.get("num_trades", 0)},
        {"Metric": "Avg Trade Duration (days)", "Value": metrics.get("avg_trade_duration_days", 0.0)},
    ])

    # Set Metric as index
    df = df.set_index("Metric")

    # Apply formatting
    styler = df.style.format({
        "Value": lambda x: _format_metric_value(x, df.loc[df["Value"] == x].index[0] if x in df["Value"].values else "")
    })

    # Custom formatting based on metric type
    def format_value(val, metric_name):
        """Format value based on metric type."""
        if metric_name in ["Total Return", "Annualized Return", "Max Drawdown", "Win Rate"]:
            return f"{val:.2%}"
        elif metric_name == "Profit Factor":
            if val == float("inf"):
                return "∞"
            return f"{val:.2f}"
        elif metric_name == "Sharpe Ratio":
            return f"{val:.2f}"
        elif metric_name == "Number of Trades":
            return f"{int(val)}"
        else:
            return f"{val:.2f}"

    # Create formatted strings
    formatted_data = []
    for idx, row in df.iterrows():
        formatted_data.append({
            "Metric": idx,
            "Value": format_value(row["Value"], idx)
        })

    df_formatted = pd.DataFrame(formatted_data).set_index("Metric")

    # Apply styling with colors
    def color_negative_red(val):
        """Color negative values red, positive green."""
        try:
            # Extract numeric value from formatted string
            if "%" in val:
                num_val = float(val.replace("%", ""))
            elif val == "∞":
                return "color: green"
            else:
                num_val = float(val)

            if num_val < 0:
                return "color: red"
            elif num_val > 0:
                return "color: green"
        except (ValueError, AttributeError):
            pass
        return ""

    styler = df_formatted.style.map(color_negative_red, subset=["Value"])

    return styler


def _format_metric_value(value, metric_name):
    """Helper to format individual metric values."""
    if metric_name in ["Total Return", "Annualized Return", "Max Drawdown", "Win Rate"]:
        return f"{value:.2%}"
    elif metric_name == "Profit Factor":
        if value == float("inf"):
            return "∞"
        return f"{value:.2f}"
    elif metric_name == "Sharpe Ratio":
        return f"{value:.2f}"
    elif metric_name == "Number of Trades":
        return f"{int(value)}"
    else:
        return f"{value:.2f}"


def compare_stats(run1: "Run", run2: "Run"):
    """Create side-by-side comparison of metrics from two runs.

    Args:
        run1: First run to compare
        run2: Second run to compare

    Returns:
        Styled pandas DataFrame with side-by-side metrics
    """
    metrics1 = run1.metrics
    metrics2 = run2.metrics

    # Create comparison DataFrame
    df = pd.DataFrame([
        {
            "Metric": "Total Return",
            run1.strategy_name: metrics1.get("total_return", 0.0),
            run2.strategy_name: metrics2.get("total_return", 0.0),
        },
        {
            "Metric": "Annualized Return",
            run1.strategy_name: metrics1.get("annualized_return", 0.0),
            run2.strategy_name: metrics2.get("annualized_return", 0.0),
        },
        {
            "Metric": "Sharpe Ratio",
            run1.strategy_name: metrics1.get("sharpe_ratio", 0.0),
            run2.strategy_name: metrics2.get("sharpe_ratio", 0.0),
        },
        {
            "Metric": "Max Drawdown",
            run1.strategy_name: metrics1.get("max_drawdown", 0.0),
            run2.strategy_name: metrics2.get("max_drawdown", 0.0),
        },
        {
            "Metric": "Win Rate",
            run1.strategy_name: metrics1.get("win_rate", 0.0),
            run2.strategy_name: metrics2.get("win_rate", 0.0),
        },
        {
            "Metric": "Profit Factor",
            run1.strategy_name: metrics1.get("profit_factor", 0.0),
            run2.strategy_name: metrics2.get("profit_factor", 0.0),
        },
        {
            "Metric": "Number of Trades",
            run1.strategy_name: metrics1.get("num_trades", 0),
            run2.strategy_name: metrics2.get("num_trades", 0),
        },
        {
            "Metric": "Avg Trade Duration (days)",
            run1.strategy_name: metrics1.get("avg_trade_duration_days", 0.0),
            run2.strategy_name: metrics2.get("avg_trade_duration_days", 0.0),
        },
    ])

    df = df.set_index("Metric")

    # Format values based on metric type
    def format_comparison_value(val, metric_name):
        """Format value based on metric type."""
        if metric_name in ["Total Return", "Annualized Return", "Max Drawdown", "Win Rate"]:
            return f"{val:.2%}"
        elif metric_name == "Profit Factor":
            if val == float("inf"):
                return "∞"
            return f"{val:.2f}"
        elif metric_name == "Sharpe Ratio":
            return f"{val:.2f}"
        elif metric_name == "Number of Trades":
            return f"{int(val)}"
        else:
            return f"{val:.2f}"

    # Create formatted DataFrame
    formatted_data = []
    for idx, row in df.iterrows():
        formatted_data.append({
            "Metric": idx,
            run1.strategy_name: format_comparison_value(row[run1.strategy_name], idx),
            run2.strategy_name: format_comparison_value(row[run2.strategy_name], idx),
        })

    df_formatted = pd.DataFrame(formatted_data).set_index("Metric")

    # Highlight better values
    def highlight_better(row):
        """Highlight the better value in each row."""
        metric_name = row.name
        val1_str = row[run1.strategy_name]
        val2_str = row[run2.strategy_name]

        # Extract numeric values
        try:
            if "%" in val1_str:
                val1 = float(val1_str.replace("%", ""))
                val2 = float(val2_str.replace("%", ""))
            elif val1_str == "∞" or val2_str == "∞":
                val1 = float("inf") if val1_str == "∞" else float(val1_str)
                val2 = float("inf") if val2_str == "∞" else float(val2_str)
            else:
                val1 = float(val1_str)
                val2 = float(val2_str)

            # Determine which is better (for max_drawdown, less negative is better)
            if metric_name == "Max Drawdown":
                better_idx = 0 if val1 > val2 else 1  # Less negative is better
            else:
                better_idx = 0 if val1 > val2 else 1  # Higher is better

            if better_idx == 0:
                return ["background-color: rgba(0, 255, 0, 0.2)", ""]
            else:
                return ["", "background-color: rgba(0, 255, 0, 0.2)"]
        except (ValueError, AttributeError):
            return ["", ""]

    styler = df_formatted.style.apply(highlight_better, axis=1)

    return styler
