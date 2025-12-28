"""Run class for managing backtest runs."""

import random
import string
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pandas as pd

from lynx.exceptions import ValidationError

if TYPE_CHECKING:
    import plotly.graph_objects as go


# Required columns for trades DataFrame
REQUIRED_TRADES_COLUMNS = [
    "symbol",
    "entry_date",
    "exit_date",
    "entry_price",
    "exit_price",
    "return",
]


def _validate_trades(df: Any) -> None:
    """Validate trades DataFrame has required columns.

    Args:
        df: Input to validate

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(df, pd.DataFrame):
        raise ValidationError("trades must be a DataFrame")

    missing_cols = set(REQUIRED_TRADES_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValidationError(
            f"trades DataFrame is missing required columns: {sorted(missing_cols)}"
        )


def _generate_run_id(strategy_name: str) -> str:
    """Generate a unique run ID.

    Format: {strategy}_{YYYYMMDD_HHMMSS}_{4-char-random}

    Args:
        strategy_name: Name of the strategy

    Returns:
        Unique run ID string
    """
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{strategy_name}_{timestamp}_{random_suffix}"


class Run:
    """Represents a single backtest run.

    Attributes:
        id: Unique run identifier (available after save())
        strategy_name: Strategy name
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        params: Strategy parameters
        metrics: Calculated performance metrics
    """

    def __init__(
        self,
        name: str,
        params: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        notes: str | None = None,
    ) -> None:
        """Create a new Run for logging.

        Args:
            name: Strategy name
            params: Optional strategy parameters
            tags: Optional tags for filtering
            notes: Optional text notes
        """
        self._id: str | None = None
        self._strategy_name = name
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._params = params or {}
        self._tags = tags or []
        self._notes = notes
        self._trades_df: pd.DataFrame | None = None
        self._artifacts: dict[str, tuple[str, pd.DataFrame]] = {}  # name -> (type, df)
        self._metrics: dict[str, Any] = {}
        self._saved = False

    @property
    def id(self) -> str | None:
        """Unique run identifier (available after save())."""
        return self._id

    @property
    def strategy_name(self) -> str:
        """Strategy name."""
        return self._strategy_name

    @property
    def created_at(self) -> datetime:
        """Creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Last modification timestamp."""
        return self._updated_at

    @property
    def params(self) -> dict[str, Any]:
        """Strategy parameters."""
        return self._params

    @property
    def metrics(self) -> dict[str, Any]:
        """Calculated performance metrics."""
        return self._metrics

    def trades(self, df: pd.DataFrame) -> "Run":
        """Set the trades DataFrame.

        Args:
            df: DataFrame with columns: symbol, entry_date, exit_date,
                entry_price, exit_price, return

        Returns:
            self (for method chaining)

        Raises:
            ValidationError: If required columns are missing
        """
        _validate_trades(df)
        self._trades_df = df.copy()
        return self

    def signal(self, name: str, df: pd.DataFrame) -> "Run":
        """Add a signal DataFrame as artifact.

        Args:
            name: Signal name (e.g., "entry", "exit")
            df: Boolean DataFrame with symbols as columns, dates as index

        Returns:
            self (for method chaining)
        """
        self._artifacts[name] = ("signal", df.copy())
        return self

    def data(self, name: str, df: pd.DataFrame) -> "Run":
        """Add a data DataFrame as artifact.

        Args:
            name: Data name (e.g., "close_price", "volume")
            df: DataFrame with symbols as columns, dates as index

        Returns:
            self (for method chaining)
        """
        self._artifacts[name] = ("data", df.copy())
        return self

    def save(self) -> "Run":
        """Persist the run to storage.

        Returns:
            self (for method chaining)

        Raises:
            ValidationError: If trades not set
        """
        if self._trades_df is None:
            raise ValidationError("trades must be set before saving")

        # Update timestamp on every save
        self._updated_at = datetime.now()

        # Generate run ID if not already set
        if self._id is None:
            self._id = _generate_run_id(self._strategy_name)

        # Save to database
        self._save_to_db()
        self._saved = True

        return self

    def _save_to_db(self) -> None:
        """Save run and artifacts to SQLite and Parquet storage."""
        from lynx.metrics import calculate_all
        from lynx.storage import parquet, sqlite

        # Calculate metrics from trades
        self._metrics = calculate_all(self._trades_df)  # type: ignore

        # Insert run record into SQLite
        sqlite.insert_run(
            run_id=self._id,  # type: ignore
            strategy_name=self._strategy_name,
            created_at=self._created_at,
            updated_at=self._updated_at,
            metrics=self._metrics,
            params=self._params if self._params else None,
            tags=self._tags if self._tags else None,
            notes=self._notes,
        )

        # Save trades artifact
        file_path = parquet.save_artifact(self._id, "trades", self._trades_df)  # type: ignore
        sqlite.insert_artifact(
            run_id=self._id,  # type: ignore
            name="trades",
            artifact_type="trades",
            file_path=file_path,
            rows=len(self._trades_df),  # type: ignore
            columns=list(self._trades_df.columns),  # type: ignore
        )

        # Save other artifacts
        for name, (artifact_type, df) in self._artifacts.items():
            file_path = parquet.save_artifact(self._id, name, df)  # type: ignore
            sqlite.insert_artifact(
                run_id=self._id,  # type: ignore
                name=name,
                artifact_type=artifact_type,
                file_path=file_path,
                rows=len(df),
                columns=list(df.columns),
            )

    def get_trades(self) -> pd.DataFrame:
        """Get the trades DataFrame.

        Returns:
            Trades DataFrame
        """
        if not self._saved:
            # Return in-memory version
            if self._trades_df is None:
                raise ValidationError("trades not set")
            return self._trades_df.copy()

        # Load from storage
        from lynx.storage import parquet, sqlite

        artifacts = sqlite.get_artifacts(self._id)  # type: ignore
        trades_artifact = next((a for a in artifacts if a["name"] == "trades"), None)
        if trades_artifact is None:
            raise ValidationError("trades artifact not found")

        return parquet.load_artifact(trades_artifact["file_path"])

    def get_signal(self, name: str) -> pd.DataFrame:
        """Get a signal DataFrame by name.

        Args:
            name: Signal name

        Returns:
            Signal DataFrame
        """
        if not self._saved:
            # Return in-memory version
            if name not in self._artifacts:
                raise ValidationError(f"signal '{name}' not found")
            artifact_type, df = self._artifacts[name]
            if artifact_type != "signal":
                raise ValidationError(f"'{name}' is not a signal artifact")
            return df.copy()

        # Load from storage
        from lynx.storage import parquet, sqlite

        artifacts = sqlite.get_artifacts(self._id)  # type: ignore
        artifact = next((a for a in artifacts if a["name"] == name), None)
        if artifact is None:
            raise ValidationError(f"artifact '{name}' not found")
        if artifact["artifact_type"] != "signal":
            raise ValidationError(f"'{name}' is not a signal artifact")

        return parquet.load_artifact(artifact["file_path"])

    def get_data(self, name: str) -> pd.DataFrame:
        """Get a data DataFrame by name.

        Args:
            name: Data name

        Returns:
            Data DataFrame
        """
        if not self._saved:
            # Return in-memory version
            if name not in self._artifacts:
                raise ValidationError(f"data '{name}' not found")
            artifact_type, df = self._artifacts[name]
            if artifact_type != "data":
                raise ValidationError(f"'{name}' is not a data artifact")
            return df.copy()

        # Load from storage
        from lynx.storage import parquet, sqlite

        artifacts = sqlite.get_artifacts(self._id)  # type: ignore
        artifact = next((a for a in artifacts if a["name"] == name), None)
        if artifact is None:
            raise ValidationError(f"artifact '{name}' not found")
        if artifact["artifact_type"] != "data":
            raise ValidationError(f"'{name}' is not a data artifact")

        return parquet.load_artifact(artifact["file_path"])

    def list_artifacts(self) -> list[str]:
        """List all artifact names for this run.

        Returns:
            List of artifact names
        """
        if not self._saved:
            # Return in-memory version
            artifacts = ["trades"] if self._trades_df is not None else []
            artifacts.extend(self._artifacts.keys())
            return artifacts

        # Load from storage
        from lynx.storage import sqlite

        artifacts = sqlite.get_artifacts(self._id)  # type: ignore
        return [a["name"] for a in artifacts]

    def stats(self):
        """Display metrics table in Jupyter.

        Shows formatted table with: total_return, annualized_return, sharpe_ratio,
        max_drawdown, win_rate, profit_factor, num_trades, avg_trade_duration

        Returns:
            Styled pandas DataFrame (Styler) for Jupyter display
        """
        from lynx.display.stats import format_stats

        # If not saved yet, calculate metrics on the fly
        if not self._saved and self._trades_df is not None:
            from lynx.metrics import calculate_all

            metrics = calculate_all(self._trades_df)
        else:
            metrics = self._metrics

        return format_stats(metrics)

    def plot(self, figsize: tuple[int, int] = (10, 6)) -> "go.Figure":
        """Display interactive equity curve in Jupyter.

        Args:
            figsize: Figure size (width, height) in inches

        Returns:
            Plotly Figure object for Jupyter display
        """

        from lynx.display.plot import create_equity_curve

        trades = self.get_trades()
        return create_equity_curve(trades, self.strategy_name, figsize)

    def compare(self, other: "Run"):
        """Compare this run with another run.

        Displays side-by-side metrics comparison and overlaid equity curves.

        Args:
            other: Another Run object to compare

        Returns:
            Tuple of (metrics_comparison_styler, equity_curves_figure)
        """
        from lynx.display.plot import compare_equity_curves
        from lynx.display.stats import compare_stats

        stats_styler = compare_stats(self, other)
        plot_fig = compare_equity_curves(self, other)

        return stats_styler, plot_fig

    def explain(
        self,
        symbol: str | list[str],
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
    ):
        """Explain why a stock was or wasn't selected.

        Shows a timeline of signal conditions for the specified symbol(s),
        allowing you to understand which conditions were True/False over time.

        Args:
            symbol: Stock symbol(s) to analyze (e.g., "2330" or ["2330", "2317"])
            start_date: Optional start date filter (YYYY-MM-DD string or datetime)
            end_date: Optional end date filter (YYYY-MM-DD string or datetime)

        Returns:
            If single symbol: DataFrame with signal timeline
            If multiple symbols: Dict mapping symbol to DataFrame

        Raises:
            ValidationError: If no signal artifacts are logged

        Requires:
            At least one signal artifact logged via run.signal(name, df)

        Example:
            >>> run.explain("2330")  # Why wasn't TSMC selected?
            >>> run.explain(["2330", "2317"])  # Compare multiple stocks
            >>> run.explain("2330", start_date="2024-01-01", end_date="2024-03-01")
        """
        from lynx.display.explain import explain_symbol

        return explain_symbol(self, symbol, start_date, end_date)


@dataclass
class RunSummary:
    """Lightweight summary returned by lynx.runs().

    Attributes:
        id: Unique run identifier
        strategy_name: Strategy name
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        params: Strategy parameters
        metrics: Calculated performance metrics
        tags: List of tags for filtering
    """

    id: str
    strategy_name: str
    created_at: datetime
    updated_at: datetime
    params: dict[str, Any]
    metrics: dict[str, float]
    tags: list[str]

    def load(self) -> "Run":
        """Load the full Run object.

        Returns:
            Complete Run object with all artifacts loaded

        Raises:
            RunNotFoundError: If run_id doesn't exist
        """
        from lynx import load

        return load(self.id)
