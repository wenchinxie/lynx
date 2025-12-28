"""Tests for lynx storage layer."""

import os
from datetime import datetime

import pandas as pd
import pytest

from lynx.config import config, reset_config
from lynx.storage import delete_artifacts, init_db, load_artifact, save_artifact
from lynx.storage.sqlite import (
    delete_run,
    get_artifacts,
    get_run,
    insert_artifact,
    insert_run,
    list_runs,
)


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create a temporary storage directory for tests."""
    reset_config()
    if "LYNX_DATA_DIR" in os.environ:
        del os.environ["LYNX_DATA_DIR"]
    config(data_dir=tmp_path)
    init_db()
    yield tmp_path
    reset_config()


class TestSQLiteStorage:
    """Tests for SQLite storage operations."""

    def test_init_db_creates_tables(self, temp_storage_dir):
        """Test that init_db creates the required tables."""
        from lynx.storage.sqlite import get_connection

        conn = get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "runs" in tables
        assert "artifacts" in tables

    def test_insert_run(self, temp_storage_dir):
        """Test inserting a run record."""
        run_id = "test_strategy_20241214_120000_abc"
        strategy_name = "test_strategy"
        created_at = datetime(2024, 12, 14, 12, 0, 0)
        updated_at = datetime(2024, 12, 14, 12, 30, 0)
        params = {"threshold": 0.5, "window": 10}
        metrics = {"sharpe_ratio": 1.5, "total_return": 0.25}
        tags = ["test", "experiment"]
        notes = "Test run"

        insert_run(
            run_id=run_id,
            strategy_name=strategy_name,
            created_at=created_at,
            updated_at=updated_at,
            metrics=metrics,
            params=params,
            tags=tags,
            notes=notes,
        )

        # Verify the run was inserted
        run = get_run(run_id)
        assert run is not None
        assert run["id"] == run_id
        assert run["strategy_name"] == strategy_name
        assert run["created_at"] == created_at
        assert run["updated_at"] == updated_at
        assert run["params"] == params
        assert run["metrics"] == metrics
        assert run["tags"] == tags
        assert run["notes"] == notes

    def test_get_run_by_id(self, temp_storage_dir):
        """Test retrieving a run by ID."""
        run_id = "test_strategy_20241214_120001_xyz"
        strategy_name = "test_strategy"
        created_at = datetime(2024, 12, 14, 12, 0, 1)
        updated_at = datetime(2024, 12, 14, 12, 0, 1)
        metrics = {"sharpe_ratio": 2.0}

        insert_run(
            run_id=run_id,
            strategy_name=strategy_name,
            created_at=created_at,
            updated_at=updated_at,
            metrics=metrics,
        )

        run = get_run(run_id)
        assert run is not None
        assert run["id"] == run_id
        assert run["strategy_name"] == strategy_name

    def test_get_run_not_found(self, temp_storage_dir):
        """Test that get_run returns None for non-existent run."""
        run = get_run("nonexistent_run_id")
        assert run is None

    def test_insert_artifact(self, temp_storage_dir):
        """Test inserting artifact metadata."""
        run_id = "test_strategy_20241214_120002_def"
        strategy_name = "test_strategy"
        created_at = datetime(2024, 12, 14, 12, 0, 2)
        updated_at = datetime(2024, 12, 14, 12, 0, 2)
        metrics = {"sharpe_ratio": 1.0}

        # Insert run first
        insert_run(
            run_id=run_id,
            strategy_name=strategy_name,
            created_at=created_at,
            updated_at=updated_at,
            metrics=metrics,
        )

        # Insert artifact
        insert_artifact(
            run_id=run_id,
            name="trades",
            artifact_type="trades",
            file_path="artifacts/test_strategy_20241214_120002_def/trades.parquet",
            rows=100,
            columns=["symbol", "entry_date", "exit_date", "entry_price", "exit_price", "return"],
        )

        # Verify artifact was inserted
        artifacts = get_artifacts(run_id)
        assert len(artifacts) == 1
        assert artifacts[0]["name"] == "trades"
        assert artifacts[0]["artifact_type"] == "trades"
        assert artifacts[0]["rows"] == 100
        assert len(artifacts[0]["columns"]) == 6

    def test_get_artifacts_by_run_id(self, temp_storage_dir):
        """Test getting all artifacts for a run."""
        run_id = "test_strategy_20241214_120003_ghi"
        strategy_name = "test_strategy"
        created_at = datetime(2024, 12, 14, 12, 0, 3)
        updated_at = datetime(2024, 12, 14, 12, 0, 3)
        metrics = {"sharpe_ratio": 1.2}

        # Insert run
        insert_run(
            run_id=run_id,
            strategy_name=strategy_name,
            created_at=created_at,
            updated_at=updated_at,
            metrics=metrics,
        )

        # Insert multiple artifacts
        insert_artifact(
            run_id=run_id,
            name="trades",
            artifact_type="trades",
            file_path="artifacts/run/trades.parquet",
            rows=50,
            columns=["symbol", "entry_date"],
        )

        insert_artifact(
            run_id=run_id,
            name="signals",
            artifact_type="signal",
            file_path="artifacts/run/signals.parquet",
            rows=100,
            columns=["2330", "2317"],
        )

        # Verify we get all artifacts
        artifacts = get_artifacts(run_id)
        assert len(artifacts) == 2
        assert {a["name"] for a in artifacts} == {"trades", "signals"}

    def test_delete_run_cascades(self, temp_storage_dir):
        """Test that deleting a run removes its artifacts."""
        run_id = "test_strategy_20241214_120004_jkl"
        strategy_name = "test_strategy"
        created_at = datetime(2024, 12, 14, 12, 0, 4)
        updated_at = datetime(2024, 12, 14, 12, 0, 4)
        metrics = {"sharpe_ratio": 1.8}

        # Insert run and artifact
        insert_run(
            run_id=run_id,
            strategy_name=strategy_name,
            created_at=created_at,
            updated_at=updated_at,
            metrics=metrics,
        )

        insert_artifact(
            run_id=run_id,
            name="trades",
            artifact_type="trades",
            file_path="artifacts/run/trades.parquet",
            rows=75,
            columns=["symbol"],
        )

        # Verify artifact exists
        artifacts = get_artifacts(run_id)
        assert len(artifacts) == 1

        # Delete run
        deleted = delete_run(run_id)
        assert deleted is True

        # Verify run and artifacts are gone
        run = get_run(run_id)
        assert run is None

        artifacts = get_artifacts(run_id)
        assert len(artifacts) == 0

    def test_delete_run_returns_false_if_not_found(self, temp_storage_dir):
        """Test that delete_run returns False for non-existent run."""
        deleted = delete_run("nonexistent_run_id")
        assert deleted is False

    def test_list_runs(self, temp_storage_dir):
        """Test listing runs."""
        # Insert multiple runs
        for i in range(3):
            run_id = f"test_strategy_2024121412000{i}_run{i}"
            created_at = datetime(2024, 12, 14, 12, 0, i)
            insert_run(
                run_id=run_id,
                strategy_name="test_strategy",
                created_at=created_at,
                updated_at=created_at,
                metrics={"sharpe_ratio": float(i)},
            )

        runs = list_runs()
        assert len(runs) == 3

    def test_list_runs_filtered_by_strategy(self, temp_storage_dir):
        """Test listing runs filtered by strategy."""
        # Insert runs for different strategies
        insert_run(
            run_id="strategy_a_20241214_120000_a",
            strategy_name="strategy_a",
            created_at=datetime(2024, 12, 14, 12, 0, 0),
            updated_at=datetime(2024, 12, 14, 12, 0, 0),
            metrics={"sharpe_ratio": 1.0},
        )

        insert_run(
            run_id="strategy_b_20241214_120001_b",
            strategy_name="strategy_b",
            created_at=datetime(2024, 12, 14, 12, 0, 1),
            updated_at=datetime(2024, 12, 14, 12, 0, 1),
            metrics={"sharpe_ratio": 2.0},
        )

        insert_run(
            run_id="strategy_a_20241214_120002_c",
            strategy_name="strategy_a",
            created_at=datetime(2024, 12, 14, 12, 0, 2),
            updated_at=datetime(2024, 12, 14, 12, 0, 2),
            metrics={"sharpe_ratio": 1.5},
        )

        # Filter by strategy_a
        runs = list_runs(strategy="strategy_a")
        assert len(runs) == 2
        assert all(r["strategy_name"] == "strategy_a" for r in runs)

    def test_list_runs_with_limit(self, temp_storage_dir):
        """Test listing runs with limit."""
        # Insert multiple runs
        for i in range(5):
            created_at = datetime(2024, 12, 14, 12, 0, i)
            insert_run(
                run_id=f"test_strategy_2024121412000{i}_lim{i}",
                strategy_name="test_strategy",
                created_at=created_at,
                updated_at=created_at,
                metrics={"sharpe_ratio": float(i)},
            )

        runs = list_runs(limit=3)
        assert len(runs) == 3

    def test_list_runs_ordered(self, temp_storage_dir):
        """Test that runs are ordered by updated_at descending by default."""
        # Insert runs in non-chronological order
        times = [
            datetime(2024, 12, 14, 12, 0, 2),
            datetime(2024, 12, 14, 12, 0, 0),
            datetime(2024, 12, 14, 12, 0, 1),
        ]

        for i, created_at in enumerate(times):
            insert_run(
                run_id=f"test_strategy_{created_at.isoformat()}_ord{i}",
                strategy_name="test_strategy",
                created_at=created_at,
                updated_at=created_at,
                metrics={"sharpe_ratio": float(i)},
            )

        runs = list_runs()
        # Should be ordered by updated_at, newest to oldest
        assert runs[0]["updated_at"] == datetime(2024, 12, 14, 12, 0, 2)
        assert runs[1]["updated_at"] == datetime(2024, 12, 14, 12, 0, 1)
        assert runs[2]["updated_at"] == datetime(2024, 12, 14, 12, 0, 0)


class TestParquetStorage:
    """Tests for Parquet storage operations."""

    def test_save_artifact_creates_file(self, temp_storage_dir, sample_trades_df):
        """Test that save_artifact creates a Parquet file."""
        run_id = "test_run_123"
        artifact_name = "trades"

        file_path = save_artifact(run_id, artifact_name, sample_trades_df)

        # Verify file path format
        assert "artifacts" in file_path
        assert run_id in file_path
        assert artifact_name in file_path
        assert file_path.endswith(".parquet")

        # Verify file exists
        from lynx.storage.parquet import get_artifacts_dir

        full_path = get_artifacts_dir() / run_id / f"{artifact_name}.parquet"
        assert full_path.exists()

    def test_load_artifact_returns_dataframe(self, temp_storage_dir, sample_trades_df):
        """Test that load_artifact returns the correct DataFrame."""
        run_id = "test_run_456"
        artifact_name = "trades"

        # Save artifact
        file_path = save_artifact(run_id, artifact_name, sample_trades_df)

        # Load artifact
        loaded_df = load_artifact(file_path)

        # Verify data matches
        pd.testing.assert_frame_equal(loaded_df, sample_trades_df)

    def test_delete_artifacts_removes_directory(self, temp_storage_dir, sample_trades_df):
        """Test that delete_artifacts removes the run's artifact directory."""
        run_id = "test_run_789"

        # Save multiple artifacts
        save_artifact(run_id, "trades", sample_trades_df)
        save_artifact(run_id, "signals", sample_trades_df)

        from lynx.storage.parquet import get_artifacts_dir

        artifact_dir = get_artifacts_dir() / run_id
        assert artifact_dir.exists()

        # Delete artifacts
        delete_artifacts(run_id)

        # Verify directory is removed
        assert not artifact_dir.exists()

    def test_delete_artifacts_nonexistent_run(self, temp_storage_dir):
        """Test that delete_artifacts handles non-existent run gracefully."""
        # Should not raise an error
        delete_artifacts("nonexistent_run_id")

    def test_save_artifact_with_index(self, temp_storage_dir, sample_signal_df):
        """Test that save_artifact preserves DataFrame index."""
        run_id = "test_run_index"
        artifact_name = "signals"

        file_path = save_artifact(run_id, artifact_name, sample_signal_df)
        loaded_df = load_artifact(file_path)

        # Verify index values are preserved (freq attribute may differ after roundtrip)
        assert list(loaded_df.index) == list(sample_signal_df.index)
        # Verify data is preserved
        pd.testing.assert_frame_equal(
            loaded_df.reset_index(drop=True),
            sample_signal_df.reset_index(drop=True)
        )
