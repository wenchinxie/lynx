"""Unit tests for CLI commands."""

import pytest
from click.testing import CliRunner

import lynx
from lynx.cli import cli
from lynx.config import config, reset_config
from lynx.storage import sqlite


class TestCLIList:
    """Test lynx list command."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, temp_data_dir):
        """Set up and tear down test environment."""
        reset_config()
        config(data_dir=temp_data_dir)
        sqlite.init_db()
        yield
        reset_config()

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_list_empty(self, runner):
        """Test list command with no runs."""
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "No runs found" in result.output or result.output.strip() == ""

    def test_list_with_runs(self, runner, sample_trades_df):
        """Test list command with saved runs."""
        lynx.log("strategy1", trades=sample_trades_df)
        lynx.log("strategy2", trades=sample_trades_df)

        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "strategy1" in result.output
        assert "strategy2" in result.output

    def test_list_filter_by_strategy(self, runner, sample_trades_df):
        """Test list command with strategy filter."""
        lynx.log("strategy1", trades=sample_trades_df)
        lynx.log("strategy2", trades=sample_trades_df)

        result = runner.invoke(cli, ["list", "--strategy", "strategy1"])
        assert result.exit_code == 0
        assert "strategy1" in result.output
        assert "strategy2" not in result.output

    def test_list_with_limit(self, runner, sample_trades_df):
        """Test list command with limit."""
        for i in range(5):
            lynx.log(f"strategy{i}", trades=sample_trades_df)

        result = runner.invoke(cli, ["list", "--limit", "3"])
        assert result.exit_code == 0
        # Output should only show 3 runs


class TestCLIShow:
    """Test lynx show command."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, temp_data_dir):
        """Set up and tear down test environment."""
        reset_config()
        config(data_dir=temp_data_dir)
        sqlite.init_db()
        yield
        reset_config()

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_show_existing_run(self, runner, sample_trades_df):
        """Test show command for existing run."""
        run = lynx.log("test_strategy", trades=sample_trades_df, params={"threshold": 50})

        result = runner.invoke(cli, ["show", run.id])
        assert result.exit_code == 0
        assert run.id in result.output
        assert "test_strategy" in result.output
        assert "threshold" in result.output or "50" in result.output

    def test_show_nonexistent_run(self, runner):
        """Test show command for non-existent run."""
        result = runner.invoke(cli, ["show", "nonexistent_run_id"])
        assert result.exit_code != 0 or "not found" in result.output.lower()


class TestCLIDelete:
    """Test lynx delete command."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, temp_data_dir):
        """Set up and tear down test environment."""
        reset_config()
        config(data_dir=temp_data_dir)
        sqlite.init_db()
        yield
        reset_config()

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_delete_existing_run(self, runner, sample_trades_df):
        """Test delete command for existing run."""
        run = lynx.log("test_strategy", trades=sample_trades_df)
        run_id = run.id

        result = runner.invoke(cli, ["delete", run_id], input="y\n")
        assert result.exit_code == 0
        assert "deleted" in result.output.lower() or "success" in result.output.lower()

        # Verify run is deleted
        from lynx.exceptions import RunNotFoundError
        with pytest.raises(RunNotFoundError):
            lynx.load(run_id)

    def test_delete_nonexistent_run(self, runner):
        """Test delete command for non-existent run."""
        result = runner.invoke(cli, ["delete", "nonexistent_run_id"], input="y\n")
        assert result.exit_code != 0 or "not found" in result.output.lower()


class TestCLIExport:
    """Test lynx export command."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, temp_data_dir):
        """Set up and tear down test environment."""
        reset_config()
        config(data_dir=temp_data_dir)
        sqlite.init_db()
        yield
        reset_config()

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_export_existing_run(self, runner, sample_trades_df, tmp_path):
        """Test export command for existing run."""
        run = lynx.log("test_strategy", trades=sample_trades_df)

        output_dir = tmp_path / "export"
        result = runner.invoke(cli, ["export", run.id, "--output", str(output_dir)])

        assert result.exit_code == 0
        assert output_dir.exists()
        # Should have at least trades.csv or trades.parquet
        files = list(output_dir.iterdir())
        assert len(files) > 0

    def test_export_nonexistent_run(self, runner, tmp_path):
        """Test export command for non-existent run."""
        output_dir = tmp_path / "export"
        result = runner.invoke(cli, ["export", "nonexistent_run_id", "--output", str(output_dir)])
        assert result.exit_code != 0 or "not found" in result.output.lower()


class TestCLIServe:
    """Test lynx serve command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_serve_help(self, runner):
        """Test serve command help."""
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output
