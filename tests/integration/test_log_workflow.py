"""Integration tests for lynx.log() workflow."""


import pandas as pd
import pytest

import lynx
from lynx.config import config, reset_config
from lynx.exceptions import ValidationError
from lynx.storage import sqlite


class TestLogWorkflow:
    """Test the complete lynx.log() workflow."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, temp_data_dir):
        """Set up and tear down test environment."""
        reset_config()
        config(data_dir=temp_data_dir)
        sqlite.init_db()
        yield
        reset_config()

    def test_log_basic_workflow(self, sample_trades_df):
        """Test basic log workflow with just trades."""
        run = lynx.log("test_strategy", trades=sample_trades_df)

        # Should return a Run object
        assert isinstance(run, lynx.Run)
        assert run.id is not None
        assert run.id.startswith("test_strategy_")
        assert run.strategy_name == "test_strategy"
        assert run.metrics is not None
        assert "total_return" in run.metrics
        assert "sharpe_ratio" in run.metrics

    def test_log_with_params_and_tags(self, sample_trades_df):
        """Test log with parameters and tags."""
        params = {"threshold": 50, "lookback": 20}
        tags = ["production", "v1.0"]

        run = lynx.log(
            "test_strategy",
            trades=sample_trades_df,
            params=params,
            tags=tags,
        )

        assert run.params == params
        # Tags should be stored (will add tags property in Run class)

    def test_log_with_notes(self, sample_trades_df):
        """Test log with notes."""
        notes = "This is a test run with some notes."

        run = lynx.log(
            "test_strategy",
            trades=sample_trades_df,
            notes=notes,
        )

        # Notes should be stored (will add notes property in Run class)
        assert run is not None

    def test_log_with_artifacts(self, sample_trades_df, sample_signal_df, sample_price_df):
        """Test log with additional artifacts."""
        run = lynx.log(
            "test_strategy",
            trades=sample_trades_df,
            entry_signal=sample_signal_df,
            close_price=sample_price_df,
        )

        assert run is not None
        assert run.id is not None

    def test_log_invalid_trades_raises_error(self):
        """Test that invalid trades DataFrame raises ValidationError."""
        invalid_df = pd.DataFrame({
            "symbol": ["2330", "2317"],
            "entry_date": ["2024-01-01", "2024-01-02"],
            # Missing other required columns
        })

        with pytest.raises(ValidationError):
            lynx.log("test_strategy", trades=invalid_df)

    def test_log_persists_to_storage(self, sample_trades_df, temp_data_dir):
        """Test that log() persists data to storage."""
        run = lynx.log("test_strategy", trades=sample_trades_df)

        # Verify SQLite record exists
        stored_run = sqlite.get_run(run.id)
        assert stored_run is not None
        assert stored_run["strategy_name"] == "test_strategy"
        assert stored_run["metrics"] is not None

        # Verify artifacts exist
        artifacts = sqlite.get_artifacts(run.id)
        assert len(artifacts) >= 1  # At least trades artifact
        assert any(a["name"] == "trades" for a in artifacts)

        # Verify Parquet files exist
        artifacts_dir = temp_data_dir / "artifacts" / run.id
        assert artifacts_dir.exists()
        assert (artifacts_dir / "trades.parquet").exists()


class TestRunWorkflow:
    """Test the complete Run() workflow with method chaining."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, temp_data_dir):
        """Set up and tear down test environment."""
        reset_config()
        config(data_dir=temp_data_dir)
        sqlite.init_db()
        yield
        reset_config()

    def test_run_basic_workflow(self, sample_trades_df):
        """Test basic Run workflow."""
        run = lynx.Run("test_strategy")
        run.trades(sample_trades_df)
        run.save()

        # Should have ID after save
        assert run.id is not None
        assert run.id.startswith("test_strategy_")

    def test_run_method_chaining(self, sample_trades_df, sample_signal_df):
        """Test method chaining."""
        run = (
            lynx.Run("test_strategy")
            .trades(sample_trades_df)
            .signal("entry", sample_signal_df)
            .save()
        )

        assert run.id is not None

    def test_run_with_params_and_tags(self, sample_trades_df):
        """Test Run with parameters and tags."""
        params = {"threshold": 50, "lookback": 20}
        tags = ["production", "v1.0"]
        notes = "Test run notes"

        run = lynx.Run(
            "test_strategy",
            params=params,
            tags=tags,
            notes=notes,
        )
        run.trades(sample_trades_df).save()

        assert run.params == params

    def test_run_save_without_trades_raises_error(self):
        """Test that saving without trades raises ValidationError."""
        run = lynx.Run("test_strategy")

        with pytest.raises(ValidationError):
            run.save()

    def test_run_persists_all_artifacts(
        self, sample_trades_df, sample_signal_df, sample_price_df, temp_data_dir
    ):
        """Test that all artifacts are persisted."""
        run = (
            lynx.Run("test_strategy")
            .trades(sample_trades_df)
            .signal("entry", sample_signal_df)
            .data("close_price", sample_price_df)
            .save()
        )

        # Verify all artifacts in SQLite
        artifacts = sqlite.get_artifacts(run.id)
        artifact_names = {a["name"] for a in artifacts}
        assert "trades" in artifact_names
        assert "entry" in artifact_names
        assert "close_price" in artifact_names

        # Verify all Parquet files
        artifacts_dir = temp_data_dir / "artifacts" / run.id
        assert (artifacts_dir / "trades.parquet").exists()
        assert (artifacts_dir / "entry.parquet").exists()
        assert (artifacts_dir / "close_price.parquet").exists()

    def test_run_get_trades(self, sample_trades_df):
        """Test getting trades back from Run."""
        run = lynx.Run("test_strategy").trades(sample_trades_df).save()

        retrieved_trades = run.get_trades()
        assert isinstance(retrieved_trades, pd.DataFrame)
        assert len(retrieved_trades) == len(sample_trades_df)
        pd.testing.assert_frame_equal(
            retrieved_trades.reset_index(drop=True),
            sample_trades_df.reset_index(drop=True),
        )

    def test_run_get_signal(self, sample_trades_df, sample_signal_df):
        """Test getting signal artifact."""
        run = (
            lynx.Run("test_strategy")
            .trades(sample_trades_df)
            .signal("entry", sample_signal_df)
            .save()
        )

        retrieved_signal = run.get_signal("entry")
        assert isinstance(retrieved_signal, pd.DataFrame)
        # Compare values and shape (ignore index frequency metadata)
        pd.testing.assert_frame_equal(
            retrieved_signal, sample_signal_df, check_freq=False
        )

    def test_run_get_data(self, sample_trades_df, sample_price_df):
        """Test getting data artifact."""
        run = (
            lynx.Run("test_strategy")
            .trades(sample_trades_df)
            .data("close_price", sample_price_df)
            .save()
        )

        retrieved_data = run.get_data("close_price")
        assert isinstance(retrieved_data, pd.DataFrame)
        # Compare values and shape (ignore index frequency metadata)
        pd.testing.assert_frame_equal(
            retrieved_data, sample_price_df, check_freq=False
        )

    def test_run_list_artifacts(self, sample_trades_df, sample_signal_df, sample_price_df):
        """Test listing all artifacts."""
        run = (
            lynx.Run("test_strategy")
            .trades(sample_trades_df)
            .signal("entry", sample_signal_df)
            .data("close_price", sample_price_df)
            .save()
        )

        artifacts = run.list_artifacts()
        assert isinstance(artifacts, list)
        assert "trades" in artifacts
        assert "entry" in artifacts
        assert "close_price" in artifacts
