"""SQLite storage for run metadata."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def get_db_path() -> Path:
    """Get the path to the SQLite database."""
    from lynx.config import get_data_dir

    return get_data_dir() / "lynx.db"


def _migrate_add_updated_at(conn: sqlite3.Connection) -> None:
    """Migration: Add updated_at column to runs table if not exists.

    This migration:
    1. Adds the updated_at column
    2. Backfills existing rows with created_at value
    3. Creates indexes for efficient sorting/filtering
    """
    # Check if column already exists
    cursor = conn.execute("PRAGMA table_info(runs)")
    columns = [row[1] for row in cursor.fetchall()]

    if "updated_at" not in columns:
        # Add column without default (SQLite limitation for non-constant defaults)
        conn.execute("ALTER TABLE runs ADD COLUMN updated_at TIMESTAMP")
        # Backfill: set updated_at = created_at for existing rows
        conn.execute("UPDATE runs SET updated_at = created_at WHERE updated_at IS NULL")
        conn.commit()

    # Create indexes (IF NOT EXISTS handles idempotency)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_updated_at ON runs(updated_at)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_runs_strategy_updated ON runs(strategy_name, updated_at)"
    )
    conn.commit()


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    # Ensure the data directory exists
    from lynx.config import ensure_data_dir
    ensure_data_dir()

    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            strategy_name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            params TEXT,
            metrics TEXT NOT NULL,
            tags TEXT,
            notes TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_runs_strategy_name ON runs(strategy_name);
        CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at);

        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            artifact_type TEXT NOT NULL CHECK(artifact_type IN ('trades', 'signal', 'data')),
            file_path TEXT NOT NULL,
            rows INTEGER NOT NULL,
            columns TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(run_id, name)
        );

        CREATE INDEX IF NOT EXISTS idx_artifacts_run_id ON artifacts(run_id);

        -- Strategy watchlists table (FR-035)
        CREATE TABLE IF NOT EXISTS strategy_watchlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(strategy_name, symbol)
        );

        CREATE INDEX IF NOT EXISTS idx_watchlist_strategy ON strategy_watchlists(strategy_name);

        -- Portfolio holdings table (FR-036)
        CREATE TABLE IF NOT EXISTS portfolio_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            quantity REAL,
            added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON portfolio_holdings(symbol);
    """)
    conn.commit()

    # Run migrations for existing databases
    _migrate_add_updated_at(conn)

    conn.close()


def insert_run(
    run_id: str,
    strategy_name: str,
    created_at: datetime,
    updated_at: datetime,
    metrics: dict[str, Any],
    params: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    notes: str | None = None,
) -> None:
    """Insert a new run record."""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO runs (id, strategy_name, created_at, updated_at, params, metrics, tags, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            strategy_name,
            created_at.isoformat(timespec="milliseconds"),
            updated_at.isoformat(timespec="milliseconds"),
            json.dumps(params) if params else None,
            json.dumps(metrics),
            json.dumps(tags) if tags else None,
            notes,
        ),
    )
    conn.commit()
    conn.close()


def get_run(run_id: str) -> dict | None:
    """Get a run by ID, returns None if not found."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row["id"],
        "strategy_name": row["strategy_name"],
        "created_at": datetime.fromisoformat(row["created_at"]),
        "updated_at": datetime.fromisoformat(row["updated_at"]),
        "params": json.loads(row["params"]) if row["params"] else None,
        "metrics": json.loads(row["metrics"]),
        "tags": json.loads(row["tags"]) if row["tags"] else None,
        "notes": row["notes"],
    }


def update_run_timestamp(run_id: str, updated_at: datetime) -> bool:
    """Update the updated_at timestamp for a run.

    Args:
        run_id: Run identifier
        updated_at: New timestamp value

    Returns:
        True if run was found and updated, False otherwise
    """
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE runs SET updated_at = ? WHERE id = ?",
        (updated_at.isoformat(timespec="milliseconds"), run_id),
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def insert_artifact(
    run_id: str,
    name: str,
    artifact_type: str,
    file_path: str,
    rows: int,
    columns: list[str],
) -> None:
    """Insert artifact metadata."""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO artifacts (run_id, name, artifact_type, file_path, rows, columns)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (run_id, name, artifact_type, file_path, rows, json.dumps(columns)),
    )
    conn.commit()
    conn.close()


def get_artifacts(run_id: str) -> list[dict]:
    """Get all artifacts for a run."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM artifacts WHERE run_id = ? ORDER BY created_at", (run_id,)
    ).fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "run_id": row["run_id"],
            "name": row["name"],
            "artifact_type": row["artifact_type"],
            "file_path": row["file_path"],
            "rows": row["rows"],
            "columns": json.loads(row["columns"]),
            "created_at": datetime.fromisoformat(row["created_at"]),
        }
        for row in rows
    ]


def delete_run(run_id: str) -> bool:
    """Delete a run and cascade to artifacts. Returns True if deleted."""
    conn = get_connection()
    cursor = conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def list_runs(
    strategy: str | None = None,
    start_date: datetime | str | None = None,
    end_date: datetime | str | None = None,
    date_field: str = "updated_at",
    limit: int | None = None,
    order_by: str = "updated_at",
    descending: bool = True,
) -> list[dict]:
    """List runs with optional filtering.

    Args:
        strategy: Filter by strategy name (optional)
        start_date: Filter runs on or after this date (optional)
        end_date: Filter runs on or before this date (optional)
        date_field: Which field to filter on ("updated_at" or "created_at")
        limit: Maximum number of runs to return (optional)
        order_by: Field to sort by (default: "updated_at"). Supports both
                  database columns and metrics fields (e.g., "sharpe_ratio")
        descending: Sort order (default: True = newest first)

    Returns:
        List of run dictionaries with all fields including updated_at

    Raises:
        ValueError: If date_field is not "updated_at" or "created_at"
        ValueError: If date format is invalid
    """
    # Validate date_field
    valid_date_fields = {"updated_at", "created_at"}
    if date_field not in valid_date_fields:
        raise ValueError(
            f"Invalid date_field '{date_field}'. Must be one of: {valid_date_fields}"
        )

    # Database columns that can be sorted directly in SQL
    db_columns = {"id", "strategy_name", "created_at", "updated_at"}
    sort_in_python = order_by not in db_columns

    conn = get_connection()

    # Build query
    query = "SELECT * FROM runs"
    params: list[Any] = []
    conditions: list[str] = []

    if strategy is not None:
        conditions.append("strategy_name = ?")
        params.append(strategy)

    # Date filtering with validation
    if start_date is not None:
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date)
            except ValueError as e:
                raise ValueError(f"Invalid start_date format: {e}") from e
        conditions.append(f"{date_field} >= ?")
        params.append(start_date.isoformat(timespec="milliseconds"))

    if end_date is not None:
        if isinstance(end_date, str):
            try:
                end_date = datetime.fromisoformat(end_date)
            except ValueError as e:
                raise ValueError(f"Invalid end_date format: {e}") from e
        conditions.append(f"{date_field} <= ?")
        params.append(end_date.isoformat(timespec="milliseconds"))

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Add ordering - only for database columns, metrics sorted in Python
    direction = "DESC" if descending else "ASC"
    if not sort_in_python:
        query += f" ORDER BY {order_by} {direction}, id {direction}"
    else:
        # Default ordering for metrics sort (will be re-sorted in Python)
        query += " ORDER BY updated_at DESC, id DESC"

    # Add limit only if sorting by database column (metrics need all rows first)
    if limit is not None and not sort_in_python:
        query += " LIMIT ?"
        params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = [
        {
            "id": row["id"],
            "strategy_name": row["strategy_name"],
            "created_at": datetime.fromisoformat(row["created_at"]),
            "updated_at": datetime.fromisoformat(row["updated_at"]),
            "params": json.loads(row["params"]) if row["params"] else None,
            "metrics": json.loads(row["metrics"]),
            "tags": json.loads(row["tags"]) if row["tags"] else None,
            "notes": row["notes"],
        }
        for row in rows
    ]

    # Sort by metrics field in Python if needed
    if sort_in_python:
        results.sort(
            key=lambda r: r["metrics"].get(order_by) or 0,
            reverse=descending,
        )
        # Apply limit after Python sorting
        if limit is not None:
            results = results[:limit]

    return results


# Watchlist functions (T055-T058)


def get_watchlist(strategy_name: str) -> list[str]:
    """Get the watchlist symbols for a strategy.

    Args:
        strategy_name: Strategy identifier

    Returns:
        List of stock symbols in the watchlist
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT symbol FROM strategy_watchlists WHERE strategy_name = ? ORDER BY symbol",
        (strategy_name,),
    ).fetchall()
    conn.close()
    return [row["symbol"] for row in rows]


def set_watchlist(strategy_name: str, symbols: list[str]) -> None:
    """Set the watchlist for a strategy, replacing any existing entries.

    Args:
        strategy_name: Strategy identifier
        symbols: List of stock symbols
    """
    conn = get_connection()

    # Remove existing entries
    conn.execute(
        "DELETE FROM strategy_watchlists WHERE strategy_name = ?",
        (strategy_name,),
    )

    # Insert new entries
    now = datetime.now().isoformat(timespec="milliseconds")
    for symbol in symbols:
        conn.execute(
            "INSERT INTO strategy_watchlists (strategy_name, symbol, added_at) VALUES (?, ?, ?)",
            (strategy_name, symbol, now),
        )

    conn.commit()
    conn.close()


def add_to_watchlist(strategy_name: str, symbol: str) -> bool:
    """Add a symbol to a strategy's watchlist.

    Args:
        strategy_name: Strategy identifier
        symbol: Stock symbol to add

    Returns:
        True if added, False if already exists
    """
    conn = get_connection()
    now = datetime.now().isoformat(timespec="milliseconds")

    try:
        conn.execute(
            "INSERT INTO strategy_watchlists (strategy_name, symbol, added_at) VALUES (?, ?, ?)",
            (strategy_name, symbol, now),
        )
        conn.commit()
        added = True
    except sqlite3.IntegrityError:
        # Already exists (UNIQUE constraint)
        added = False

    conn.close()
    return added


def remove_from_watchlist(strategy_name: str, symbol: str) -> bool:
    """Remove a symbol from a strategy's watchlist.

    Args:
        strategy_name: Strategy identifier
        symbol: Stock symbol to remove

    Returns:
        True if removed, False if not found
    """
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM strategy_watchlists WHERE strategy_name = ? AND symbol = ?",
        (strategy_name, symbol),
    )
    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return removed


# Portfolio functions (T059-T060)


def get_portfolio() -> list[dict]:
    """Get all portfolio holdings.

    Returns:
        List of dicts with symbol and quantity
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT symbol, quantity FROM portfolio_holdings ORDER BY symbol"
    ).fetchall()
    conn.close()
    return [{"symbol": row["symbol"], "quantity": row["quantity"]} for row in rows]


def set_portfolio(holdings: list[dict]) -> None:
    """Set portfolio holdings, replacing any existing entries.

    Args:
        holdings: List of dicts with 'symbol' and optional 'quantity' keys

    Example:
        >>> set_portfolio([{"symbol": "2330", "quantity": 1000}, {"symbol": "2317"}])
    """
    conn = get_connection()

    # Remove existing entries
    conn.execute("DELETE FROM portfolio_holdings")

    # Insert new entries
    now = datetime.now().isoformat(timespec="milliseconds")
    for holding in holdings:
        symbol = holding["symbol"]
        quantity = holding.get("quantity")
        conn.execute(
            "INSERT INTO portfolio_holdings (symbol, quantity, added_at, updated_at) VALUES (?, ?, ?, ?)",
            (symbol, quantity, now, now),
        )

    conn.commit()
    conn.close()
