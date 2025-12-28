"""Metrics calculations for backtest analysis."""
from typing import Any

import numpy as np
import pandas as pd


def total_return(trades: pd.DataFrame) -> float:
    """Calculate total cumulative return.

    Compounds individual trade returns: (1+r1)*(1+r2)*...-1

    Args:
        trades: DataFrame with 'return' column containing individual trade returns

    Returns:
        Total cumulative return as a float
    """
    if trades.empty:
        return 0.0
    returns = trades["return"].values
    cumulative = np.prod(1 + returns) - 1
    return float(cumulative)


def annualized_return(trades: pd.DataFrame) -> float:
    """Calculate annualized return.

    Based on trading period from first entry to last exit.
    Assumes 252 trading days per year.

    Args:
        trades: DataFrame with 'return', 'entry_date', and 'exit_date' columns

    Returns:
        Annualized return as a float
    """
    if trades.empty:
        return 0.0
    total = total_return(trades)
    first_entry = trades["entry_date"].min()
    last_exit = trades["exit_date"].max()
    days = (last_exit - first_entry).days
    if days <= 0:
        return 0.0
    years = days / 365.0
    return float((1 + total) ** (1 / years) - 1) if years > 0 else 0.0


def sharpe_ratio(trades: pd.DataFrame, risk_free_rate: float = 0.0) -> float:
    """Calculate Sharpe ratio.

    Uses individual trade returns, annualized.

    Args:
        trades: DataFrame with 'return', 'entry_date', and 'exit_date' columns
        risk_free_rate: Annual risk-free rate (default: 0.0)

    Returns:
        Sharpe ratio as a float
    """
    if trades.empty or len(trades) < 2:
        return 0.0
    returns = trades["return"]
    excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
    mean_return = excess_returns.mean()
    std_return = excess_returns.std()
    if std_return == 0:
        return 0.0
    # Annualize: multiply by sqrt(252) for daily returns
    # But our returns are per-trade, so adjust based on avg trade duration
    avg_duration = avg_trade_duration(trades)
    trades_per_year = 252 / avg_duration if avg_duration > 0 else 252
    return float(mean_return / std_return * np.sqrt(trades_per_year))


def max_drawdown(trades: pd.DataFrame) -> float:
    """Calculate maximum drawdown.

    Returns negative value (e.g., -0.15 for 15% drawdown).

    Args:
        trades: DataFrame with 'return' and 'entry_date' columns

    Returns:
        Maximum drawdown as a negative float (or 0.0 if no drawdown)
    """
    if trades.empty:
        return 0.0
    # Sort by entry date and calculate cumulative returns
    sorted_trades = trades.sort_values("entry_date")
    returns = sorted_trades["return"].values
    cumulative = np.cumprod(1 + returns)
    peak = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - peak) / peak
    return float(drawdown.min())


def win_rate(trades: pd.DataFrame) -> float:
    """Calculate win rate (percentage of profitable trades).

    Args:
        trades: DataFrame with 'return' column

    Returns:
        Win rate as a float between 0.0 and 1.0
    """
    if trades.empty:
        return 0.0
    wins = (trades["return"] > 0).sum()
    return float(wins / len(trades))


def profit_factor(trades: pd.DataFrame) -> float:
    """Calculate profit factor (gross profit / gross loss).

    Returns inf if no losing trades.

    Args:
        trades: DataFrame with 'return' column

    Returns:
        Profit factor as a float (inf if no losses, 0.0 if no profits)
    """
    if trades.empty:
        return 0.0
    gross_profit = trades.loc[trades["return"] > 0, "return"].sum()
    gross_loss = abs(trades.loc[trades["return"] < 0, "return"].sum())
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return float(gross_profit / gross_loss)


def num_trades(trades: pd.DataFrame) -> int:
    """Return total number of trades.

    Args:
        trades: DataFrame containing trade data

    Returns:
        Number of trades as an integer
    """
    return len(trades)


def avg_trade_duration(trades: pd.DataFrame) -> float:
    """Calculate average trade duration in days.

    Args:
        trades: DataFrame with 'entry_date' and 'exit_date' columns

    Returns:
        Average trade duration in days as a float
    """
    if trades.empty:
        return 0.0
    durations = (trades["exit_date"] - trades["entry_date"]).dt.days
    return float(durations.mean())


def calculate_all(trades: pd.DataFrame) -> dict[str, Any]:
    """Calculate all metrics for a trades DataFrame.

    Args:
        trades: DataFrame with columns: 'return', 'entry_date', 'exit_date'

    Returns:
        dict with keys: total_return, annualized_return, sharpe_ratio,
        max_drawdown, win_rate, profit_factor, num_trades, avg_trade_duration_days
    """
    return {
        "total_return": total_return(trades),
        "annualized_return": annualized_return(trades),
        "sharpe_ratio": sharpe_ratio(trades),
        "max_drawdown": max_drawdown(trades),
        "win_rate": win_rate(trades),
        "profit_factor": profit_factor(trades),
        "num_trades": num_trades(trades),
        "avg_trade_duration_days": avg_trade_duration(trades),
    }
