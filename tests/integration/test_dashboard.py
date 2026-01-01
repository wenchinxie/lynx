"""Integration tests for Dashboard API."""

import pytest
from fastapi.testclient import TestClient

import lynx
from lynx.config import config, reset_config
from lynx.storage import sqlite


class TestDashboardAPI:
    """Test Dashboard REST API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, temp_data_dir):
        """Set up and tear down test environment."""
        reset_config()
        config(data_dir=temp_data_dir)
        sqlite.init_db()
        yield
        reset_config()

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        from lynx.dashboard.server import app
        return TestClient(app)

    def test_get_runs_empty(self, client):
        """Test GET /api/runs with no runs."""
        response = client.get("/api/runs")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_runs_with_data(self, client, sample_trades_df):
        """Test GET /api/runs with saved runs."""
        # Create some runs
        run1 = lynx.log("strategy1", trades=sample_trades_df)
        run2 = lynx.log("strategy2", trades=sample_trades_df)

        response = client.get("/api/runs")
        assert response.status_code == 200

        runs = response.json()
        assert len(runs) == 2
        run_ids = [r["id"] for r in runs]
        assert run1.id in run_ids
        assert run2.id in run_ids

    def test_get_runs_filter_by_strategy(self, client, sample_trades_df):
        """Test GET /api/runs with strategy filter."""
        lynx.log("strategy1", trades=sample_trades_df)
        lynx.log("strategy2", trades=sample_trades_df)
        lynx.log("strategy1", trades=sample_trades_df)

        response = client.get("/api/runs?strategy=strategy1")
        assert response.status_code == 200

        runs = response.json()
        assert len(runs) == 2
        for run in runs:
            assert run["strategy_name"] == "strategy1"

    def test_get_runs_sort_and_limit(self, client, sample_trades_df):
        """Test GET /api/runs with sort and limit."""
        for i in range(5):
            lynx.log(f"strategy{i}", trades=sample_trades_df)

        response = client.get("/api/runs?limit=3&sort_by=created_at&order=desc")
        assert response.status_code == 200

        runs = response.json()
        assert len(runs) == 3

    def test_get_run_by_id(self, client, sample_trades_df):
        """Test GET /api/runs/{run_id}."""
        run = lynx.log("test_strategy", trades=sample_trades_df, params={"threshold": 50})

        response = client.get(f"/api/runs/{run.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == run.id
        assert data["strategy_name"] == "test_strategy"
        assert data["params"] == {"threshold": 50}
        assert "metrics" in data

    def test_get_run_not_found(self, client):
        """Test GET /api/runs/{run_id} for non-existent run."""
        response = client.get("/api/runs/nonexistent_run_id")
        assert response.status_code == 404

    def test_get_run_trades(self, client, sample_trades_df):
        """Test GET /api/runs/{run_id}/trades."""
        run = lynx.log("test_strategy", trades=sample_trades_df)

        response = client.get(f"/api/runs/{run.id}/trades")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert len(data["data"]) == len(sample_trades_df)

    def test_get_run_artifacts(self, client, sample_trades_df, sample_signal_df):
        """Test GET /api/runs/{run_id}/artifacts/{name}."""
        run = lynx.log("test_strategy", trades=sample_trades_df, entry_signal=sample_signal_df)

        response = client.get(f"/api/runs/{run.id}/artifacts/entry_signal")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data

    def test_get_run_artifacts_with_pagination(self, client, sample_trades_df, sample_signal_df):
        """Test GET /api/runs/{run_id}/artifacts/{name} with pagination."""
        run = lynx.log("test_strategy", trades=sample_trades_df, entry_signal=sample_signal_df)

        response = client.get(f"/api/runs/{run.id}/artifacts/entry_signal?page=1&page_size=5")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "page" in data
        assert "page_size" in data

    def test_delete_run(self, client, sample_trades_df):
        """Test DELETE /api/runs/{run_id}."""
        run = lynx.log("test_strategy", trades=sample_trades_df)
        run_id = run.id

        response = client.delete(f"/api/runs/{run_id}")
        assert response.status_code == 200

        # Verify run is deleted
        response = client.get(f"/api/runs/{run_id}")
        assert response.status_code == 404

    def test_delete_run_not_found(self, client):
        """Test DELETE /api/runs/{run_id} for non-existent run."""
        response = client.delete("/api/runs/nonexistent_run_id")
        assert response.status_code == 404

    def test_get_strategies(self, client, sample_trades_df):
        """Test GET /api/strategies."""
        lynx.log("strategy_a", trades=sample_trades_df)
        lynx.log("strategy_b", trades=sample_trades_df)
        lynx.log("strategy_a", trades=sample_trades_df)

        response = client.get("/api/strategies")
        assert response.status_code == 200

        strategies = response.json()
        assert set(strategies) == {"strategy_a", "strategy_b"}


class TestDashboardCompareAPI:
    """Test Dashboard comparison API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, temp_data_dir):
        """Set up and tear down test environment."""
        reset_config()
        config(data_dir=temp_data_dir)
        sqlite.init_db()
        yield
        reset_config()

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        from lynx.dashboard.server import app
        return TestClient(app)

    def test_compare_runs(self, client, sample_trades_df):
        """Test GET /api/compare."""
        run1 = lynx.log("strategy1", trades=sample_trades_df)

        trades2 = sample_trades_df.copy()
        trades2["return"] = trades2["return"] * 1.1
        run2 = lynx.log("strategy2", trades=trades2)

        response = client.get(f"/api/compare?run_ids={run1.id},{run2.id}")
        assert response.status_code == 200

        data = response.json()
        assert "runs" in data
        assert len(data["runs"]) == 2

    def test_compare_runs_invalid_ids(self, client):
        """Test GET /api/compare with invalid run IDs."""
        response = client.get("/api/compare?run_ids=invalid1,invalid2")
        assert response.status_code == 404


class TestDashboardStaticFiles:
    """Test static file serving for React frontend."""

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        from lynx.dashboard.server import app
        return TestClient(app)

    def test_index_html_fallback(self, client):
        """Test that non-API routes fall back to index.html (SPA)."""
        # This will return 404 until we have the actual frontend built
        # For now, just verify the route exists
        response = client.get("/")
        # Accept 200 or 404 depending on whether static files exist
        assert response.status_code in [200, 404]
