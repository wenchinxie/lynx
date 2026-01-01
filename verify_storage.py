#!/usr/bin/env python3
"""Quick verification script for storage layer implementation."""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

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


def test_basic_functionality():
    """Test basic storage functionality."""
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        reset_config()
        config(data_dir=tmpdir)
        init_db()

        # Test 1: Insert and retrieve run
        print("Test 1: Insert and retrieve run...")
        run_id = "test_strategy_20241214_120000_abc"
        insert_run(
            run_id=run_id,
            strategy_name="test_strategy",
            created_at=datetime(2024, 12, 14, 12, 0, 0),
            metrics={"sharpe_ratio": 1.5, "total_return": 0.25},
            params={"threshold": 0.5},
        )

        run = get_run(run_id)
        assert run is not None
        assert run["id"] == run_id
        print("  ✓ Run insert/retrieve works")

        # Test 2: Save and load artifact
        print("\nTest 2: Save and load artifact...")
        df = pd.DataFrame(
            {
                "symbol": ["2330", "2317"],
                "entry_date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
                "exit_date": pd.to_datetime(["2024-01-05", "2024-01-08"]),
                "entry_price": [580.0, 45.0],
                "exit_price": [595.0, 44.0],
                "return": [0.0259, -0.0222],
            }
        )

        file_path = save_artifact(run_id, "trades", df)
        loaded_df = load_artifact(file_path)
        pd.testing.assert_frame_equal(loaded_df, df)
        print("  ✓ Artifact save/load works")

        # Test 3: Artifact metadata
        print("\nTest 3: Artifact metadata...")
        insert_artifact(
            run_id=run_id,
            name="trades",
            artifact_type="trades",
            file_path=file_path,
            rows=len(df),
            columns=list(df.columns),
        )

        artifacts = get_artifacts(run_id)
        assert len(artifacts) == 1
        assert artifacts[0]["name"] == "trades"
        print("  ✓ Artifact metadata works")

        # Test 4: List runs
        print("\nTest 4: List runs...")
        runs = list_runs()
        assert len(runs) == 1
        assert runs[0]["id"] == run_id
        print("  ✓ List runs works")

        # Test 5: Delete run cascade
        print("\nTest 5: Delete run cascade...")
        deleted = delete_run(run_id)
        assert deleted is True
        run = get_run(run_id)
        assert run is None
        artifacts = get_artifacts(run_id)
        assert len(artifacts) == 0
        print("  ✓ Delete cascade works")

        print("\n✅ All basic tests passed!")


if __name__ == "__main__":
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
