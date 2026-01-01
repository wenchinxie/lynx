"""FastAPI server for the Lynx dashboard."""

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

import lynx
from lynx.exceptions import RunNotFoundError
from lynx.storage import sqlite

# FastAPI app
app = FastAPI(
    title="Lynx Dashboard API",
    description="REST API for browsing and comparing backtest runs",
    version="0.1.0",
)


# Middleware to update last request time (T073)
class RequestTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to track last request time for idle timeout."""

    async def dispatch(self, request: Request, call_next):
        from lynx.dashboard import update_last_request_time

        # Update last request time on each request
        update_last_request_time()

        response = await call_next(request)
        return response


# Add request time tracking middleware
app.add_middleware(RequestTimeMiddleware)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Routes


@app.get("/api/runs")
def list_runs(
    strategy: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_by: str = "updated_at",
    order: str = "desc",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """List all runs with optional filtering.

    Args:
        strategy: Filter by strategy name
        start_date: Filter runs on or after this date (ISO 8601)
        end_date: Filter runs on or before this date (ISO 8601)
        sort_by: Column to sort by (updated_at, created_at, sharpe_ratio, etc.)
        order: Sort order (asc or desc)
        limit: Maximum number of runs to return

    Returns:
        List of run summaries with updated_at_relative field
    """
    from lynx.display.time_format import format_relative_time

    # Ensure database is initialized
    sqlite.init_db()

    descending = order.lower() == "desc"

    runs = lynx.runs(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        order_by=sort_by,
        descending=descending,
        limit=limit,
    )

    return [
        {
            "id": r.id,
            "strategy_name": r.strategy_name,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            "updated_at_relative": format_relative_time(r.updated_at),
            "params": r.params,
            "metrics": r.metrics,
            "tags": r.tags,
        }
        for r in runs
    ]


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    """Get detailed information about a specific run.

    Args:
        run_id: The run's unique identifier

    Returns:
        Run details including params and metrics

    Raises:
        HTTPException: If run not found
    """
    sqlite.init_db()

    try:
        run = lynx.load(run_id)
    except RunNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from err

    return {
        "id": run.id,
        "strategy_name": run.strategy_name,
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
        "params": run.params,
        "metrics": run.metrics,
        "artifacts": run.list_artifacts(),
    }


@app.get("/api/runs/{run_id}/metrics")
def get_run_metrics(run_id: str) -> dict[str, Any]:
    """Get categorized and formatted metrics for a run.

    Args:
        run_id: The run's unique identifier

    Returns:
        Metrics organized by category with health indicators

    Raises:
        HTTPException: If run not found
    """
    from lynx.display.health import CATEGORY_ORDER, DEFAULT_TAB, categorize_metrics

    sqlite.init_db()

    try:
        run = lynx.load(run_id)
    except RunNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from err

    metrics_by_category = categorize_metrics(run.metrics)

    return {
        "run_id": run.id,
        "metrics_by_category": metrics_by_category,
        "category_order": CATEGORY_ORDER,
        "default_tab": DEFAULT_TAB,
    }


@app.get("/api/runs/{run_id}/trades")
def get_run_trades(
    run_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Get trades DataFrame for a run.

    Args:
        run_id: The run's unique identifier
        page: Page number (1-indexed)
        page_size: Number of rows per page

    Returns:
        Paginated trades data

    Raises:
        HTTPException: If run not found
    """
    sqlite.init_db()

    try:
        run = lynx.load(run_id)
    except RunNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from err

    trades = run.get_trades()
    total_rows = len(trades)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    page_data = trades.iloc[start:end]

    return {
        "data": _dataframe_to_records(page_data),
        "total_rows": total_rows,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_rows + page_size - 1) // page_size,
    }


@app.get("/api/runs/{run_id}/artifacts/{name}")
def get_run_artifact(
    run_id: str,
    name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    symbols: str | None = None,
) -> dict[str, Any]:
    """Get an artifact DataFrame for a run.

    Args:
        run_id: The run's unique identifier
        name: Artifact name
        page: Page number (1-indexed)
        page_size: Number of rows per page
        symbols: Comma-separated list of symbols to filter

    Returns:
        Paginated artifact data

    Raises:
        HTTPException: If run or artifact not found
    """
    sqlite.init_db()

    try:
        run = lynx.load(run_id)
    except RunNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from err

    # Determine if it's a signal or data artifact
    try:
        df = run.get_signal(name)
    except Exception:
        try:
            df = run.get_data(name)
        except Exception as err:
            raise HTTPException(status_code=404, detail=f"Artifact '{name}' not found") from err

    # Filter by symbols if specified
    if symbols:
        symbol_list = [s.strip() for s in symbols.split(",")]
        valid_symbols = [s for s in symbol_list if s in df.columns]
        if valid_symbols:
            df = df[valid_symbols]

    total_rows = len(df)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    page_data = df.iloc[start:end]

    return {
        "data": _dataframe_to_records(page_data),
        "columns": list(df.columns),
        "total_rows": total_rows,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_rows + page_size - 1) // page_size,
    }


@app.delete("/api/runs/{run_id}")
def delete_run(run_id: str) -> dict[str, str]:
    """Delete a run and its artifacts.

    Args:
        run_id: The run's unique identifier

    Returns:
        Success message

    Raises:
        HTTPException: If run not found
    """
    sqlite.init_db()

    try:
        lynx.delete(run_id)
    except RunNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from err

    return {"status": "deleted", "run_id": run_id}


@app.get("/api/strategies")
def list_strategies() -> list[str]:
    """Get list of unique strategy names.

    Returns:
        List of strategy names for filter dropdown
    """
    sqlite.init_db()

    runs = lynx.runs()
    strategies = sorted({r.strategy_name for r in runs})
    return strategies


@app.get("/api/strategies/summary")
def list_strategies_summary() -> list[dict[str, Any]]:
    """Get strategy summaries with aggregated metrics.

    Returns:
        List of strategy summaries with run count and key metrics
    """
    from lynx.display.time_format import format_relative_time

    sqlite.init_db()

    runs = lynx.runs()
    if not runs:
        return []

    # Group runs by strategy
    strategies: dict[str, list] = {}
    for run in runs:
        if run.strategy_name not in strategies:
            strategies[run.strategy_name] = []
        strategies[run.strategy_name].append(run)

    summaries = []
    for strategy_name, strategy_runs in sorted(strategies.items()):
        # Get metrics from all runs
        returns = [r.metrics.get("total_return") for r in strategy_runs if r.metrics.get("total_return") is not None]
        sharpes = [r.metrics.get("sharpe_ratio") for r in strategy_runs if r.metrics.get("sharpe_ratio") is not None]
        drawdowns = [r.metrics.get("max_drawdown") for r in strategy_runs if r.metrics.get("max_drawdown") is not None]

        # Find latest run
        latest_run = max(strategy_runs, key=lambda r: r.updated_at)

        summaries.append({
            "strategy_name": strategy_name,
            "run_count": len(strategy_runs),
            "last_updated": latest_run.updated_at.isoformat(),
            "last_updated_relative": format_relative_time(latest_run.updated_at),
            "metrics": {
                "best_return": max(returns) if returns else None,
                "avg_return": sum(returns) / len(returns) if returns else None,
                "avg_sharpe": sum(sharpes) / len(sharpes) if sharpes else None,
                "best_sharpe": max(sharpes) if sharpes else None,
                "worst_drawdown": min(drawdowns) if drawdowns else None,
            },
        })

    return summaries


@app.get("/api/compare")
def compare_runs(
    run_ids: str = Query(..., description="Comma-separated run IDs"),
) -> dict[str, Any]:
    """Compare multiple runs.

    Args:
        run_ids: Comma-separated list of run IDs

    Returns:
        Combined metrics and equity data for comparison

    Raises:
        HTTPException: If any run not found
    """
    sqlite.init_db()

    ids = [r.strip() for r in run_ids.split(",")]
    runs_data = []

    for run_id in ids:
        try:
            run = lynx.load(run_id)
        except RunNotFoundError as err:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from err

        runs_data.append({
            "id": run.id,
            "strategy_name": run.strategy_name,
            "params": run.params,
            "metrics": run.metrics,
        })

    return {"runs": runs_data}


# Watchlist endpoints (T066-T067)


@app.get("/api/watchlists/{strategy_name}")
def get_watchlist(strategy_name: str) -> dict[str, Any]:
    """Get the watchlist for a strategy.

    Args:
        strategy_name: Strategy identifier

    Returns:
        Watchlist symbols and count
    """
    sqlite.init_db()

    symbols = sqlite.get_watchlist(strategy_name)
    return {
        "strategy_name": strategy_name,
        "symbols": symbols,
        "count": len(symbols),
    }


@app.put("/api/watchlists/{strategy_name}")
def set_watchlist(strategy_name: str, symbols: list[str]) -> dict[str, Any]:
    """Set the watchlist for a strategy.

    Args:
        strategy_name: Strategy identifier
        symbols: List of stock symbols

    Returns:
        Updated watchlist info
    """
    sqlite.init_db()

    sqlite.set_watchlist(strategy_name, symbols)
    return {
        "strategy_name": strategy_name,
        "symbols": symbols,
        "count": len(symbols),
        "status": "updated",
    }


# Portfolio endpoints (T068-T069)


@app.get("/api/portfolio")
def get_portfolio() -> dict[str, Any]:
    """Get portfolio holdings.

    Returns:
        List of holdings with symbol and quantity
    """
    sqlite.init_db()

    holdings = sqlite.get_portfolio()
    return {
        "holdings": holdings,
        "count": len(holdings),
    }


@app.put("/api/portfolio")
def set_portfolio(holdings: list[dict]) -> dict[str, Any]:
    """Set portfolio holdings.

    Args:
        holdings: List of dicts with 'symbol' and optional 'quantity'

    Returns:
        Updated portfolio info
    """
    sqlite.init_db()

    sqlite.set_portfolio(holdings)
    return {
        "holdings": holdings,
        "count": len(holdings),
        "status": "updated",
    }


# Coverage analysis endpoint (T070)


@app.get("/api/runs/{run_id}/monthly-returns")
def get_run_monthly_returns(run_id: str) -> dict[str, Any]:
    """Get monthly returns calculated from trades for a run.

    Args:
        run_id: The run's unique identifier

    Returns:
        Monthly returns organized by year and month

    Raises:
        HTTPException: If run not found
    """
    sqlite.init_db()

    try:
        run = lynx.load(run_id)
    except RunNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from err

    trades = run.get_trades()
    if trades.empty or "exit_date" not in trades.columns or "return" not in trades.columns:
        return {
            "run_id": run.id,
            "strategy_name": run.strategy_name,
            "monthly_returns": {},
        }

    # Convert exit_date to datetime if needed
    trades = trades.copy()
    trades["exit_date"] = pd.to_datetime(trades["exit_date"])
    trades["year"] = trades["exit_date"].dt.year
    trades["month"] = trades["exit_date"].dt.month

    # Group by year and month, sum returns
    monthly = trades.groupby(["year", "month"])["return"].sum()

    # Convert to nested dict {year: {month: return}}
    monthly_returns: dict[int, dict[int, float]] = {}
    for (year, month), ret in monthly.items():
        year = int(year)
        month = int(month)
        if year not in monthly_returns:
            monthly_returns[year] = {}
        monthly_returns[year][month] = float(ret)

    return {
        "run_id": run.id,
        "strategy_name": run.strategy_name,
        "monthly_returns": monthly_returns,
    }


@app.get("/api/runs/{run_id}/coverage")
def get_run_coverage(run_id: str) -> dict[str, Any]:
    """Get coverage analysis for a run.

    Compares run's traded symbols against strategy watchlist and user portfolio.

    Args:
        run_id: The run's unique identifier

    Returns:
        Coverage analysis with watchlist and portfolio metrics

    Raises:
        HTTPException: If run not found
    """
    from lynx.display.coverage import calculate_coverage

    sqlite.init_db()

    try:
        run = lynx.load(run_id)
    except RunNotFoundError as err:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from err

    # Get traded symbols from run
    trades = run.get_trades()
    strategy_symbols = trades["symbol"].unique().tolist() if "symbol" in trades.columns else []

    # Get watchlist for this strategy
    watchlist_symbols = sqlite.get_watchlist(run.strategy_name)

    # Get portfolio holdings
    portfolio_holdings = sqlite.get_portfolio()
    portfolio_symbols = [h["symbol"] for h in portfolio_holdings]

    # Calculate coverage
    coverage = calculate_coverage(
        strategy_symbols=strategy_symbols,
        watchlist_symbols=watchlist_symbols,
        portfolio_symbols=portfolio_symbols,
    )

    return {
        "run_id": run.id,
        "strategy_name": run.strategy_name,
        "strategy_symbols": sorted(strategy_symbols),
        "coverage": {
            "watchlist": {
                "total": len(watchlist_symbols),
                "held": coverage.watchlist_held,
                "missed": coverage.watchlist_missed,
                "coverage_pct": coverage.watchlist_coverage_pct,
            },
            "portfolio": {
                "total": len(portfolio_symbols),
                "overlap": coverage.portfolio_overlap,
                "gaps": coverage.portfolio_gaps,
                "coverage_pct": coverage.portfolio_coverage_pct,
            },
        },
    }


# Static file serving for React frontend


def _dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert DataFrame to list of records with proper serialization.

    Args:
        df: DataFrame to convert

    Returns:
        List of dicts with serialized values
    """
    # Reset index to include it in records
    df_reset = df.reset_index()

    # Convert to records
    records = df_reset.to_dict(orient="records")

    # Serialize datetime and other special types
    for record in records:
        for key, value in record.items():
            if isinstance(value, pd.Timestamp):
                record[key] = value.isoformat()
            elif pd.isna(value):
                record[key] = None

    return records


# Static files (mount after API routes)
static_dir = Path(__file__).parent / "static"


def _setup_static_files():
    """Set up static file serving if the frontend is built."""
    if static_dir.exists():
        assets_dir = static_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


# Try to set up static files
_setup_static_files()


@app.get("/")
@app.get("/{full_path:path}")
def serve_spa(full_path: str = ""):
    """Serve React SPA - all non-API routes return index.html."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")

    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    # Return placeholder if frontend not built
    return {
        "message": "Lynx Dashboard",
        "note": "Frontend not built. Use API endpoints at /api/*",
        "endpoints": [
            "GET /api/runs",
            "GET /api/runs/{run_id}",
            "GET /api/runs/{run_id}/metrics",
            "GET /api/runs/{run_id}/trades",
            "GET /api/runs/{run_id}/artifacts/{name}",
            "DELETE /api/runs/{run_id}",
            "GET /api/strategies",
            "GET /api/compare?run_ids=id1,id2",
        ],
    }
