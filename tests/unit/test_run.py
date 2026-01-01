"""Unit tests for Run class."""

from datetime import datetime

import pandas as pd
import pytest

from lynx.exceptions import ValidationError


class TestTradesValidation:
    """Test trades DataFrame validation."""

    def test_validate_trades_valid_df(self, sample_trades_df):
        """Valid trades DataFrame should pass validation."""
        from lynx.run import _validate_trades

        # Should not raise any exception
        _validate_trades(sample_trades_df)

    def test_validate_trades_missing_column(self, sample_trades_df):
        """Missing required column should raise ValidationError."""
        from lynx.run import _validate_trades

        # Remove a required column
        invalid_df = sample_trades_df.drop(columns=["symbol"])

        with pytest.raises(ValidationError) as exc_info:
            _validate_trades(invalid_df)

        assert "missing required columns" in str(exc_info.value).lower()
        assert "symbol" in str(exc_info.value)

    def test_validate_trades_multiple_missing_columns(self, sample_trades_df):
        """Multiple missing columns should be reported."""
        from lynx.run import _validate_trades

        invalid_df = sample_trades_df.drop(columns=["symbol", "entry_date"])

        with pytest.raises(ValidationError) as exc_info:
            _validate_trades(invalid_df)

        error_msg = str(exc_info.value).lower()
        assert "symbol" in error_msg
        assert "entry_date" in error_msg

    def test_validate_trades_empty_df(self, empty_trades_df):
        """Empty DataFrame with correct schema should pass."""
        from lynx.run import _validate_trades

        # Should not raise exception
        _validate_trades(empty_trades_df)

    def test_validate_trades_not_dataframe(self):
        """Non-DataFrame input should raise ValidationError."""
        from lynx.run import _validate_trades

        with pytest.raises(ValidationError) as exc_info:
            _validate_trades([1, 2, 3])  # type: ignore

        assert "dataframe" in str(exc_info.value).lower()

    def test_validate_trades_extra_columns_allowed(self, sample_trades_df):
        """Extra columns should be allowed."""
        from lynx.run import _validate_trades

        df_with_extra = sample_trades_df.copy()
        df_with_extra["extra_column"] = "extra_data"

        # Should not raise exception
        _validate_trades(df_with_extra)


class TestRunIDGeneration:
    """Test Run ID generation."""

    def test_generate_run_id_format(self):
        """Run ID should match the expected format."""
        import re

        from lynx.run import _generate_run_id

        run_id = _generate_run_id("my_strategy")

        # Format: {strategy}_{YYYYMMDD_HHMMSS}_{4-char-random}
        pattern = r"^my_strategy_\d{8}_\d{6}_[a-z0-9]{4}$"
        assert re.match(pattern, run_id), f"Invalid run_id format: {run_id}"

    def test_generate_run_id_uniqueness(self):
        """Multiple calls should generate unique IDs."""
        from lynx.run import _generate_run_id

        ids = [_generate_run_id("test") for _ in range(100)]
        assert len(set(ids)) == 100, "Run IDs should be unique"

    def test_generate_run_id_timestamp(self):
        """Run ID should contain current timestamp."""
        from datetime import datetime

        from lynx.run import _generate_run_id

        now = datetime.now()
        run_id = _generate_run_id("test")

        # Extract timestamp from run_id
        parts = run_id.split("_")
        date_part = parts[1]  # YYYYMMDD
        time_part = parts[2]  # HHMMSS

        # Check date matches (YYYYMMDD)
        expected_date = now.strftime("%Y%m%d")
        assert date_part == expected_date

    def test_generate_run_id_strategy_name(self):
        """Run ID should start with strategy name."""
        from lynx.run import _generate_run_id

        run_id = _generate_run_id("margin_transactions")
        assert run_id.startswith("margin_transactions_")


class TestRunClass:
    """Test Run class methods."""

    def test_run_init_basic(self):
        """Test basic Run initialization."""
        from lynx.run import Run

        run = Run("test_strategy")
        assert run.strategy_name == "test_strategy"
        assert run.id is None  # ID not set until save()
        assert run.params == {}
        assert run.metrics == {}
        assert run.created_at is not None

    def test_run_init_with_params(self):
        """Test Run initialization with parameters."""
        from lynx.run import Run

        params = {"threshold": 50, "lookback": 20}
        run = Run("test_strategy", params=params)
        assert run.params == params

    def test_run_init_with_tags_and_notes(self):
        """Test Run initialization with tags and notes."""
        from lynx.run import Run

        tags = ["production", "v1.0"]
        notes = "Test run notes"
        run = Run("test_strategy", tags=tags, notes=notes)
        # Tags and notes are stored internally
        assert run._tags == tags
        assert run._notes == notes

    def test_run_trades_method(self, sample_trades_df):
        """Test trades() method sets trades and returns self."""
        from lynx.run import Run

        run = Run("test_strategy")
        result = run.trades(sample_trades_df)

        # Should return self for chaining
        assert result is run
        # Trades should be set
        assert run._trades_df is not None
        assert len(run._trades_df) == len(sample_trades_df)

    def test_run_trades_validates_input(self):
        """Test trades() method validates input."""
        import pandas as pd

        from lynx.run import Run

        run = Run("test_strategy")
        invalid_df = pd.DataFrame({"invalid": [1, 2, 3]})

        with pytest.raises(ValidationError):
            run.trades(invalid_df)

    def test_run_signal_method(self, sample_signal_df):
        """Test signal() method adds signal artifact."""
        from lynx.run import Run

        run = Run("test_strategy")
        result = run.signal("entry", sample_signal_df)

        # Should return self for chaining
        assert result is run
        # Signal should be stored
        assert "entry" in run._artifacts
        assert run._artifacts["entry"][0] == "signal"

    def test_run_data_method(self, sample_price_df):
        """Test data() method adds data artifact."""
        from lynx.run import Run

        run = Run("test_strategy")
        result = run.data("close_price", sample_price_df)

        # Should return self for chaining
        assert result is run
        # Data should be stored
        assert "close_price" in run._artifacts
        assert run._artifacts["close_price"][0] == "data"

    def test_run_method_chaining(self, sample_trades_df, sample_signal_df):
        """Test that methods can be chained."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df).signal("entry", sample_signal_df)

        assert run._trades_df is not None
        assert "entry" in run._artifacts

    def test_run_save_without_trades_raises_error(self):
        """Test that save() without trades raises ValidationError."""
        from lynx.run import Run

        run = Run("test_strategy")

        with pytest.raises(ValidationError) as exc_info:
            run.save()

        assert "trades must be set" in str(exc_info.value).lower()

    def test_run_get_trades_before_save(self, sample_trades_df):
        """Test get_trades() returns in-memory data before save."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)
        retrieved = run.get_trades()

        pd.testing.assert_frame_equal(
            retrieved.reset_index(drop=True),
            sample_trades_df.reset_index(drop=True),
        )

    def test_run_get_signal_before_save(self, sample_trades_df, sample_signal_df):
        """Test get_signal() returns in-memory data before save."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df).signal("entry", sample_signal_df)
        retrieved = run.get_signal("entry")

        pd.testing.assert_frame_equal(retrieved, sample_signal_df)

    def test_run_get_data_before_save(self, sample_trades_df, sample_price_df):
        """Test get_data() returns in-memory data before save."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df).data("close_price", sample_price_df)
        retrieved = run.get_data("close_price")

        pd.testing.assert_frame_equal(retrieved, sample_price_df)

    def test_run_list_artifacts_before_save(self, sample_trades_df, sample_signal_df):
        """Test list_artifacts() returns in-memory artifacts before save."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df).signal("entry", sample_signal_df)
        artifacts = run.list_artifacts()

        assert "trades" in artifacts
        assert "entry" in artifacts

    def test_run_get_nonexistent_signal_raises_error(self, sample_trades_df):
        """Test get_signal() for non-existent signal raises error."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)

        with pytest.raises(ValidationError) as exc_info:
            run.get_signal("nonexistent")

        assert "not found" in str(exc_info.value).lower()

    def test_run_get_nonexistent_data_raises_error(self, sample_trades_df):
        """Test get_data() for non-existent data raises error."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)

        with pytest.raises(ValidationError) as exc_info:
            run.get_data("nonexistent")

        assert "not found" in str(exc_info.value).lower()


class TestRunSummary:
    """Test RunSummary dataclass."""

    def test_runsummary_init(self):
        """Test RunSummary initialization."""
        from lynx.run import RunSummary

        summary = RunSummary(
            id="test_strategy_20241214_153042_a7b2",
            strategy_name="test_strategy",
            created_at=datetime(2024, 12, 14, 15, 30, 42),
            updated_at=datetime(2024, 12, 14, 16, 45, 30),
            params={"threshold": 50},
            metrics={"total_return": 0.25, "sharpe_ratio": 1.5},
            tags=["test", "v1"],
        )

        assert summary.id == "test_strategy_20241214_153042_a7b2"
        assert summary.strategy_name == "test_strategy"
        assert summary.created_at == datetime(2024, 12, 14, 15, 30, 42)
        assert summary.updated_at == datetime(2024, 12, 14, 16, 45, 30)
        assert summary.params == {"threshold": 50}
        assert summary.metrics == {"total_return": 0.25, "sharpe_ratio": 1.5}
        assert summary.tags == ["test", "v1"]

    def test_runsummary_load(self, temp_data_dir, sample_trades_df):
        """Test RunSummary.load() returns full Run object."""
        from lynx.run import Run, RunSummary
        from lynx.storage import sqlite

        # Create and save a run
        sqlite.init_db()
        run = Run("test_strategy", params={"threshold": 50}, tags=["test"])
        run.trades(sample_trades_df).save()

        # Create RunSummary
        summary = RunSummary(
            id=run.id,
            strategy_name=run.strategy_name,
            created_at=run.created_at,
            updated_at=run.updated_at,
            params=run.params,
            metrics=run.metrics,
            tags=run._tags,
        )

        # Load full run
        loaded = summary.load()

        assert isinstance(loaded, Run)
        assert loaded.id == run.id
        assert loaded.strategy_name == run.strategy_name
        pd.testing.assert_frame_equal(
            loaded.get_trades().reset_index(drop=True),
            sample_trades_df.reset_index(drop=True),
        )


class TestDataAccessAPI:
    """Test lynx.runs(), lynx.load(), and lynx.delete() functions."""

    def test_runs_empty_database(self, temp_data_dir):
        """Test lynx.runs() returns empty list when no runs exist."""
        import lynx
        from lynx.storage import sqlite

        sqlite.init_db()
        runs = lynx.runs()

        assert runs == []

    def test_runs_returns_all_runs(self, temp_data_dir, sample_trades_df):
        """Test lynx.runs() returns all saved runs."""
        import lynx
        from lynx.storage import sqlite

        sqlite.init_db()

        # Save multiple runs
        run1 = lynx.log("strategy1", trades=sample_trades_df)
        run2 = lynx.log("strategy2", trades=sample_trades_df)

        # List all runs
        runs = lynx.runs()

        assert len(runs) == 2
        run_ids = [r.id for r in runs]
        assert run1.id in run_ids
        assert run2.id in run_ids

    def test_runs_filter_by_strategy(self, temp_data_dir, sample_trades_df):
        """Test lynx.runs() filters by strategy name."""
        import lynx
        from lynx.storage import sqlite

        sqlite.init_db()

        # Save runs with different strategies
        run1 = lynx.log("strategy1", trades=sample_trades_df)
        run2 = lynx.log("strategy2", trades=sample_trades_df)
        run3 = lynx.log("strategy1", trades=sample_trades_df)

        # Filter by strategy
        strategy1_runs = lynx.runs(strategy="strategy1")

        assert len(strategy1_runs) == 2
        for run in strategy1_runs:
            assert run.strategy_name == "strategy1"

    def test_runs_limit(self, temp_data_dir, sample_trades_df):
        """Test lynx.runs() limits number of results."""
        import lynx
        from lynx.storage import sqlite

        sqlite.init_db()

        # Save multiple runs
        for i in range(5):
            lynx.log(f"strategy{i}", trades=sample_trades_df)

        # Limit results
        runs = lynx.runs(limit=3)

        assert len(runs) == 3

    def test_runs_order_by_created_at_descending(self, temp_data_dir, sample_trades_df):
        """Test lynx.runs() orders by created_at descending by default."""
        import time

        import lynx
        from lynx.storage import sqlite

        sqlite.init_db()

        # Save runs with delays
        run1 = lynx.log("strategy1", trades=sample_trades_df)
        time.sleep(0.01)
        run2 = lynx.log("strategy2", trades=sample_trades_df)
        time.sleep(0.01)
        run3 = lynx.log("strategy3", trades=sample_trades_df)

        # Default order should be descending by created_at
        runs = lynx.runs()

        assert runs[0].id == run3.id  # Most recent first
        assert runs[1].id == run2.id
        assert runs[2].id == run1.id

    def test_runs_order_by_created_at_ascending(self, temp_data_dir, sample_trades_df):
        """Test lynx.runs() can order by created_at ascending."""
        import time

        import lynx
        from lynx.storage import sqlite

        sqlite.init_db()

        # Save runs with delays
        run1 = lynx.log("strategy1", trades=sample_trades_df)
        time.sleep(0.01)
        run2 = lynx.log("strategy2", trades=sample_trades_df)
        time.sleep(0.01)
        run3 = lynx.log("strategy3", trades=sample_trades_df)

        # Order ascending
        runs = lynx.runs(descending=False)

        assert runs[0].id == run1.id  # Oldest first
        assert runs[1].id == run2.id
        assert runs[2].id == run3.id

    def test_load_existing_run(self, temp_data_dir, sample_trades_df, sample_signal_df):
        """Test lynx.load() loads a complete run."""
        import lynx
        from lynx.storage import sqlite

        sqlite.init_db()

        # Save a run with artifacts
        run = lynx.log(
            "test_strategy",
            trades=sample_trades_df,
            params={"threshold": 50},
            tags=["test"],
            entry_signal=sample_signal_df,
        )

        # Load the run
        loaded = lynx.load(run.id)

        assert loaded.id == run.id
        assert loaded.strategy_name == "test_strategy"
        assert loaded.params == {"threshold": 50}
        assert "total_return" in loaded.metrics

        # Verify trades loaded
        pd.testing.assert_frame_equal(
            loaded.get_trades().reset_index(drop=True),
            sample_trades_df.reset_index(drop=True),
        )

        # Verify signal loaded
        loaded_signal = loaded.get_signal("entry_signal")
        pd.testing.assert_frame_equal(
            loaded_signal,
            sample_signal_df,
            check_freq=False,  # Don't check index frequency
        )

    def test_load_nonexistent_run_raises_error(self, temp_data_dir):
        """Test lynx.load() raises RunNotFoundError for invalid ID."""
        import lynx
        from lynx.exceptions import RunNotFoundError
        from lynx.storage import sqlite

        sqlite.init_db()

        with pytest.raises(RunNotFoundError) as exc_info:
            lynx.load("nonexistent_run_id")

        assert "nonexistent_run_id" in str(exc_info.value)

    def test_delete_existing_run(self, temp_data_dir, sample_trades_df):
        """Test lynx.delete() removes run from database and filesystem."""
        import lynx
        from lynx.config import get_data_dir
        from lynx.storage import sqlite

        sqlite.init_db()

        # Save a run
        run = lynx.log("test_strategy", trades=sample_trades_df)
        run_id = run.id

        # Verify artifacts directory exists
        artifacts_dir = get_data_dir() / "artifacts" / run_id
        assert artifacts_dir.exists()

        # Delete the run
        lynx.delete(run_id)

        # Verify run is deleted from database
        assert sqlite.get_run(run_id) is None

        # Verify artifacts directory is deleted
        assert not artifacts_dir.exists()

    def test_delete_nonexistent_run_raises_error(self, temp_data_dir):
        """Test lynx.delete() raises RunNotFoundError for invalid ID."""
        import lynx
        from lynx.exceptions import RunNotFoundError
        from lynx.storage import sqlite

        sqlite.init_db()

        with pytest.raises(RunNotFoundError) as exc_info:
            lynx.delete("nonexistent_run_id")

        assert "nonexistent_run_id" in str(exc_info.value)

    def test_delete_cascades_to_artifacts(self, temp_data_dir, sample_trades_df, sample_signal_df):
        """Test lynx.delete() cascades to all artifacts."""
        import lynx
        from lynx.storage import sqlite

        sqlite.init_db()

        # Save a run with multiple artifacts
        run = lynx.log(
            "test_strategy",
            trades=sample_trades_df,
            entry_signal=sample_signal_df,
        )
        run_id = run.id

        # Verify artifacts exist in database
        artifacts = sqlite.get_artifacts(run_id)
        assert len(artifacts) > 0

        # Delete the run
        lynx.delete(run_id)

        # Verify artifacts are deleted from database
        artifacts = sqlite.get_artifacts(run_id)
        assert len(artifacts) == 0
