"""Equity curve plotting for Jupyter notebooks."""

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import plotly.graph_objects as go

if TYPE_CHECKING:
    from lynx.run import Run


def create_equity_curve(
    trades: pd.DataFrame,
    strategy_name: str = "Strategy",
    figsize: tuple[int, int] = (10, 6),
) -> go.Figure:
    """Create an interactive equity curve from trades DataFrame.

    Args:
        trades: DataFrame with 'return', 'entry_date', and 'exit_date' columns
        strategy_name: Name to display in the chart
        figsize: Figure size as (width, height) in inches

    Returns:
        Plotly Figure object
    """
    if trades.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No trades to display",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 16},
        )
        fig.update_layout(
            title=f"{strategy_name} - Equity Curve",
            width=figsize[0] * 96,  # Convert inches to pixels (96 DPI)
            height=figsize[1] * 96,
        )
        return fig

    # Sort trades by entry date
    sorted_trades = trades.sort_values("entry_date").reset_index(drop=True)

    # Calculate cumulative equity
    returns = sorted_trades["return"].values
    equity = np.cumprod(1 + returns)

    # Create dates for x-axis (use exit dates for when equity changes)
    dates = [sorted_trades["entry_date"].min()]  # Start date
    dates.extend(sorted_trades["exit_date"].tolist())

    # Equity values (start at 1.0)
    equity_values = [1.0]
    equity_values.extend(equity.tolist())

    # Create figure
    fig = go.Figure()

    # Add equity curve
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=equity_values,
            mode="lines",
            name=strategy_name,
            line={"color": "#2E86DE", "width": 2},
            hovertemplate="Date: %{x|%Y-%m-%d}<br>Equity: %{y:.4f}<extra></extra>",
        )
    )

    # Add starting capital reference line
    fig.add_hline(
        y=1.0,
        line_dash="dash",
        line_color="gray",
        opacity=0.5,
        annotation_text="Starting Capital",
    )

    # Update layout
    fig.update_layout(
        title=f"{strategy_name} - Equity Curve",
        xaxis_title="Date",
        yaxis_title="Equity (Starting Capital = 1.0)",
        width=figsize[0] * 96,  # Convert inches to pixels (96 DPI)
        height=figsize[1] * 96,
        hovermode="x unified",
        template="plotly_white",
        showlegend=True,
    )

    # Format y-axis as decimal
    fig.update_yaxes(tickformat=".2f")

    return fig


def compare_equity_curves(
    run1: "Run",
    run2: "Run",
    figsize: tuple[int, int] = (10, 6),
) -> go.Figure:
    """Create overlaid equity curves for comparing two runs.

    Args:
        run1: First run to compare
        run2: Second run to compare
        figsize: Figure size as (width, height) in inches

    Returns:
        Plotly Figure object with overlaid curves
    """
    # Get trades from both runs
    trades1 = run1.get_trades()
    trades2 = run2.get_trades()

    # Create figure
    fig = go.Figure()

    # Add first equity curve
    if not trades1.empty:
        sorted_trades1 = trades1.sort_values("entry_date").reset_index(drop=True)
        returns1 = sorted_trades1["return"].values
        equity1 = np.cumprod(1 + returns1)

        dates1 = [sorted_trades1["entry_date"].min()]
        dates1.extend(sorted_trades1["exit_date"].tolist())

        equity_values1 = [1.0]
        equity_values1.extend(equity1.tolist())

        fig.add_trace(
            go.Scatter(
                x=dates1,
                y=equity_values1,
                mode="lines",
                name=run1.strategy_name,
                line={"color": "#2E86DE", "width": 2},
                hovertemplate=f"{run1.strategy_name}<br>Date: %{{x|%Y-%m-%d}}<br>Equity: %{{y:.4f}}<extra></extra>",
            )
        )

    # Add second equity curve
    if not trades2.empty:
        sorted_trades2 = trades2.sort_values("entry_date").reset_index(drop=True)
        returns2 = sorted_trades2["return"].values
        equity2 = np.cumprod(1 + returns2)

        dates2 = [sorted_trades2["entry_date"].min()]
        dates2.extend(sorted_trades2["exit_date"].tolist())

        equity_values2 = [1.0]
        equity_values2.extend(equity2.tolist())

        fig.add_trace(
            go.Scatter(
                x=dates2,
                y=equity_values2,
                mode="lines",
                name=run2.strategy_name,
                line={"color": "#FF6B6B", "width": 2},
                hovertemplate=f"{run2.strategy_name}<br>Date: %{{x|%Y-%m-%d}}<br>Equity: %{{y:.4f}}<extra></extra>",
            )
        )

    # Add starting capital reference line
    fig.add_hline(
        y=1.0,
        line_dash="dash",
        line_color="gray",
        opacity=0.5,
        annotation_text="Starting Capital",
    )

    # Update layout
    fig.update_layout(
        title=f"Comparison: {run1.strategy_name} vs {run2.strategy_name}",
        xaxis_title="Date",
        yaxis_title="Equity (Starting Capital = 1.0)",
        width=figsize[0] * 96,  # Convert inches to pixels (96 DPI)
        height=figsize[1] * 96,
        hovermode="x unified",
        template="plotly_white",
        showlegend=True,
    )

    # Format y-axis as decimal
    fig.update_yaxes(tickformat=".2f")

    return fig
