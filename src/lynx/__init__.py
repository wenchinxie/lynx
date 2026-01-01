"""Lynx - A local backtest tracking system for quantitative analysts."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from lynx.backtest import backtest
from lynx.config import config as _config
from lynx.data.exceptions import DataFetchError, InvalidSymbolError
from lynx.exceptions import RunNotFoundError
from lynx.run import Run, RunSummary
from lynx.storage import parquet, sqlite

# Public API
__all__ = [
    "log", "runs", "load", "delete", "dashboard", "config",
    "runs_today", "runs_last_7_days", "runs_last_30_days",
    "Run", "RunSummary",
    # Watchlist functions (T061)
    "get_watchlist", "set_watchlist", "add_to_watchlist", "remove_from_watchlist",
    # Portfolio functions (T062)
    "get_portfolio", "set_portfolio",
    # Backtest engine
    "backtest",
    # Data module exceptions
    "DataFetchError",
    "InvalidSymbolError",
]
__version__ = "0.1.0"


def log(
    name: str,
    *,
    trades: pd.DataFrame,
    params: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    notes: str | None = None,
    **artifacts: pd.DataFrame,
) -> Run:
    """Log a backtest run with trades and optional artifacts.

    Args:
        name: Strategy name (e.g., "margin_transactions")
        trades: DataFrame with required columns: symbol, entry_date, exit_date,
                entry_price, exit_price, return
        params: Optional dict of strategy parameters
        tags: Optional list of tags for filtering
        notes: Optional text notes
        **artifacts: Additional DataFrames to log as artifacts
                     (e.g., entry_signal=df, close_price=df)

    Returns:
        Run object with calculated metrics

    Raises:
        ValidationError: If trades DataFrame is missing required columns

    Example:
        >>> run = lynx.log("my_strategy", trades=trades_df, params={"threshold": 50})
        >>> run = lynx.log("my_strategy", trades=trades_df, entry_signal=signal_df)
    """
    # Initialize database if needed
    sqlite.init_db()

    # Create run and set trades
    run = Run(name=name, params=params, tags=tags, notes=notes)
    run.trades(trades)

    # Add artifacts
    for artifact_name, artifact_df in artifacts.items():
        # Infer artifact type based on naming convention
        # Assume 'signal' in name means it's a signal, otherwise it's data
        if "signal" in artifact_name.lower():
            run.signal(artifact_name, artifact_df)
        else:
            run.data(artifact_name, artifact_df)

    # Save and return
    run.save()
    return run


def runs(
    strategy: str | None = None,
    start_date: datetime | str | None = None,
    end_date: datetime | str | None = None,
    limit: int | None = None,
    order_by: str = "updated_at",
    descending: bool = True,
) -> list[RunSummary]:
    """List all saved runs, optionally filtered by strategy and date range.

    Args:
        strategy: Filter by strategy name (None = all strategies)
        start_date: Filter runs on or after this date (optional)
        end_date: Filter runs on or before this date (optional)
        limit: Maximum number of runs to return
        order_by: Column to sort by (default: "updated_at")
        descending: Sort in descending order (default: True = newest first)

    Returns:
        List of RunSummary objects

    Example:
        >>> all_runs = lynx.runs()
        >>> strategy_runs = lynx.runs(strategy="margin_transactions")
        >>> top_runs = lynx.runs(order_by="sharpe_ratio", limit=10)
        >>> recent = lynx.runs(start_date="2025-12-01")
    """
    # Initialize database if needed
    sqlite.init_db()

    # Query database
    run_dicts = sqlite.list_runs(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        order_by=order_by,
        descending=descending,
    )

    # Convert to RunSummary objects
    return [
        RunSummary(
            id=r["id"],
            strategy_name=r["strategy_name"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            params=r["params"] or {},
            metrics=r["metrics"],
            tags=r["tags"] or [],
        )
        for r in run_dicts
    ]


def load(run_id: str) -> Run:
    """Load a run from storage.

    Args:
        run_id: The run's unique identifier

    Returns:
        Run object with all data loaded

    Raises:
        RunNotFoundError: If run_id doesn't exist

    Example:
        >>> run = lynx.load("margin_transactions_20241214_153042_a7b2")
        >>> run.stats()
    """
    # Initialize database if needed
    sqlite.init_db()

    # Get run metadata
    run_dict = sqlite.get_run(run_id)
    if run_dict is None:
        raise RunNotFoundError(run_id)

    # Create Run object
    run = Run(
        name=run_dict["strategy_name"],
        params=run_dict["params"],
        tags=run_dict["tags"],
        notes=run_dict["notes"],
    )

    # Set run metadata
    run._id = run_dict["id"]
    run._created_at = run_dict["created_at"]
    run._updated_at = run_dict["updated_at"]
    run._metrics = run_dict["metrics"]
    run._saved = True

    # Load artifacts
    artifacts = sqlite.get_artifacts(run_id)

    # Load trades (required)
    trades_artifact = next((a for a in artifacts if a["name"] == "trades"), None)
    if trades_artifact:
        run._trades_df = parquet.load_artifact(trades_artifact["file_path"])

    # Load other artifacts
    for artifact in artifacts:
        if artifact["name"] == "trades":
            continue

        df = parquet.load_artifact(artifact["file_path"])
        run._artifacts[artifact["name"]] = (artifact["artifact_type"], df)

    return run


def delete(run_id: str) -> None:
    """Delete a run and all associated artifacts.

    Args:
        run_id: The run's unique identifier

    Raises:
        RunNotFoundError: If run_id doesn't exist

    Example:
        >>> lynx.delete("margin_transactions_20241214_153042_a7b2")
    """
    # Initialize database if needed
    sqlite.init_db()

    # Check if run exists
    run_dict = sqlite.get_run(run_id)
    if run_dict is None:
        raise RunNotFoundError(run_id)

    # Delete from database (CASCADE handles artifacts table)
    sqlite.delete_run(run_id)

    # Delete Parquet files
    parquet.delete_artifacts(run_id)


def dashboard(port: int = 8501, idle_timeout: int = 1800) -> None:
    """Launch the web dashboard.

    Args:
        port: Port number for the web server (default: 8501)
        idle_timeout: Shutdown server after this many seconds of inactivity.
                      Set to 0 to disable auto-shutdown. (default: 1800 = 30 min)

    Example:
        >>> lynx.dashboard()  # Opens browser at http://localhost:8501
        >>> lynx.dashboard(idle_timeout=0)  # Disable auto-shutdown
    """
    from lynx.dashboard import launch_dashboard
    launch_dashboard(port=port, open_browser=True, idle_timeout=idle_timeout)


def config(data_dir: str | Path | None = None) -> dict[str, Any]:
    """Get or set global configuration.

    Args:
        data_dir: Override default data directory (~/.lynx/)

    Returns:
        Current configuration dict

    Example:
        >>> lynx.config(data_dir="/custom/path")
        >>> lynx.config()  # Returns current config
    """
    return _config(data_dir)


def runs_today(strategy: str | None = None) -> list[RunSummary]:
    """Get runs updated today.

    Args:
        strategy: Optional strategy name filter

    Returns:
        List of RunSummary objects updated today

    Example:
        >>> today_runs = lynx.runs_today()
        >>> strategy_today = lynx.runs_today(strategy="margin_transactions")
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return runs(strategy=strategy, start_date=today)


def runs_last_7_days(strategy: str | None = None) -> list[RunSummary]:
    """Get runs updated in the last 7 days.

    Args:
        strategy: Optional strategy name filter

    Returns:
        List of RunSummary objects updated in the last 7 days

    Example:
        >>> recent_runs = lynx.runs_last_7_days()
        >>> strategy_recent = lynx.runs_last_7_days(strategy="margin_transactions")
    """
    start = datetime.now() - timedelta(days=7)
    return runs(strategy=strategy, start_date=start)


def runs_last_30_days(strategy: str | None = None) -> list[RunSummary]:
    """Get runs updated in the last 30 days.

    Args:
        strategy: Optional strategy name filter

    Returns:
        List of RunSummary objects updated in the last 30 days

    Example:
        >>> month_runs = lynx.runs_last_30_days()
        >>> strategy_month = lynx.runs_last_30_days(strategy="margin_transactions")
    """
    start = datetime.now() - timedelta(days=30)
    return runs(strategy=strategy, start_date=start)


# Watchlist functions (T061)


def get_watchlist(strategy_name: str) -> list[str]:
    """Get the watchlist symbols for a strategy.

    Args:
        strategy_name: Strategy name

    Returns:
        List of stock symbols in the watchlist

    Example:
        >>> watchlist = lynx.get_watchlist("margin_transactions")
        >>> print(f"Tracking {len(watchlist)} stocks")
    """
    sqlite.init_db()
    return sqlite.get_watchlist(strategy_name)


def set_watchlist(strategy_name: str, symbols: list[str]) -> None:
    """Set the watchlist for a strategy, replacing any existing entries.

    Args:
        strategy_name: Strategy name
        symbols: List of stock symbols

    Example:
        >>> lynx.set_watchlist("margin_transactions", ["2330", "2317", "2454"])
    """
    sqlite.init_db()
    sqlite.set_watchlist(strategy_name, symbols)


def add_to_watchlist(strategy_name: str, symbol: str) -> bool:
    """Add a symbol to a strategy's watchlist.

    Args:
        strategy_name: Strategy name
        symbol: Stock symbol to add

    Returns:
        True if added, False if already exists

    Example:
        >>> lynx.add_to_watchlist("margin_transactions", "2603")
    """
    sqlite.init_db()
    return sqlite.add_to_watchlist(strategy_name, symbol)


def remove_from_watchlist(strategy_name: str, symbol: str) -> bool:
    """Remove a symbol from a strategy's watchlist.

    Args:
        strategy_name: Strategy name
        symbol: Stock symbol to remove

    Returns:
        True if removed, False if not found

    Example:
        >>> lynx.remove_from_watchlist("margin_transactions", "3008")
    """
    sqlite.init_db()
    return sqlite.remove_from_watchlist(strategy_name, symbol)


# Portfolio functions (T062)


def get_portfolio() -> list[dict]:
    """Get all portfolio holdings.

    Returns:
        List of dicts with symbol and quantity

    Example:
        >>> holdings = lynx.get_portfolio()
        >>> for h in holdings:
        ...     print(f"{h['symbol']}: {h['quantity']} shares")
    """
    sqlite.init_db()
    return sqlite.get_portfolio()


def set_portfolio(holdings: list[dict]) -> None:
    """Set portfolio holdings, replacing any existing entries.

    Args:
        holdings: List of dicts with 'symbol' and optional 'quantity' keys

    Example:
        >>> lynx.set_portfolio([
        ...     {"symbol": "2330", "quantity": 1000},
        ...     {"symbol": "2317", "quantity": 500},
        ... ])
    """
    sqlite.init_db()
    sqlite.set_portfolio(holdings)
