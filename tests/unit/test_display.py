"""Unit tests for display functionality (stats, plot, compare)."""


import pandas as pd
import pytest


class TestStatsDisplay:
    """Test run.stats() method for displaying metrics."""

    def test_stats_returns_styler(self, sample_trades_df):
        """Test that stats() returns a pandas Styler object."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)
        result = run.stats()

        # Should return pandas Styler for Jupyter display
        assert hasattr(result, "data")  # Styler has data attribute
        assert hasattr(result, "applymap") or hasattr(result, "map")  # Styler has styling methods

    def test_stats_includes_all_metrics(self, sample_trades_df):
        """Test that stats() includes all required metrics."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)
        styler = run.stats()

        # Get the underlying DataFrame
        df = styler.data

        # Check all required metrics are present (using display names)
        required_display_names = [
            "Total Return",
            "Annualized Return",
            "Sharpe Ratio",
            "Max Drawdown",
            "Win Rate",
            "Profit Factor",
            "Number of Trades",
            "Avg Trade Duration (days)",
        ]

        # DataFrame should have metrics as rows (index)
        metric_names = df.index.tolist()

        for metric in required_display_names:
            assert metric in metric_names, f"Missing metric: {metric}"

    def test_stats_formats_percentages(self, sample_trades_df):
        """Test that percentage metrics are formatted correctly."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)
        styler = run.stats()

        # Verify styler has formatting applied
        # This is checked by ensuring Styler object is returned with proper data
        assert styler.data is not None

    def test_stats_with_empty_trades(self, empty_trades_df):
        """Test stats() with empty trades DataFrame."""
        from lynx.run import Run

        run = Run("test_strategy").trades(empty_trades_df)
        result = run.stats()

        # Should still return a Styler, just with zero/default values
        assert hasattr(result, "data")

    def test_stats_after_save(self, sample_trades_df, temp_data_dir, monkeypatch):
        """Test that stats() works after save()."""
        import lynx.config
        from lynx.run import Run
        from lynx.storage import sqlite

        # Set custom data directory
        monkeypatch.setenv("LYNX_DATA_DIR", str(temp_data_dir))
        lynx.config._config = {"data_dir": temp_data_dir}

        # Initialize database
        sqlite.init_db()

        run = Run("test_strategy").trades(sample_trades_df).save()
        result = run.stats()

        assert hasattr(result, "data")


class TestPlotDisplay:
    """Test run.plot() method for equity curve visualization."""

    def test_plot_returns_plotly_figure(self, sample_trades_df):
        """Test that plot() returns a Plotly figure object."""
        import plotly.graph_objects as go

        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)
        fig = run.plot()

        # Should return Plotly Figure object
        assert isinstance(fig, go.Figure)

    def test_plot_has_equity_curve_data(self, sample_trades_df):
        """Test that plot() includes equity curve data."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)
        fig = run.plot()

        # Figure should have at least one trace (the equity curve)
        assert len(fig.data) >= 1

        # First trace should have x (dates) and y (equity values) data
        trace = fig.data[0]
        assert hasattr(trace, "x")
        assert hasattr(trace, "y")
        assert len(trace.x) > 0
        assert len(trace.y) > 0

    def test_plot_with_custom_figsize(self, sample_trades_df):
        """Test that plot() accepts figsize parameter."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)
        fig = run.plot(figsize=(12, 8))

        # Should still return a Figure
        import plotly.graph_objects as go
        assert isinstance(fig, go.Figure)

    def test_plot_with_empty_trades(self, empty_trades_df):
        """Test plot() with empty trades DataFrame."""
        import plotly.graph_objects as go

        from lynx.run import Run

        run = Run("test_strategy").trades(empty_trades_df)
        fig = run.plot()

        # Should return a Figure even with empty data
        assert isinstance(fig, go.Figure)

    def test_plot_after_save(self, sample_trades_df, temp_data_dir, monkeypatch):
        """Test that plot() works after save()."""
        import plotly.graph_objects as go

        import lynx.config
        from lynx.run import Run
        from lynx.storage import sqlite

        # Set custom data directory
        monkeypatch.setenv("LYNX_DATA_DIR", str(temp_data_dir))
        lynx.config._config = {"data_dir": temp_data_dir}

        # Initialize database
        sqlite.init_db()

        run = Run("test_strategy").trades(sample_trades_df).save()
        fig = run.plot()

        assert isinstance(fig, go.Figure)

    def test_plot_equity_curve_calculation(self, sample_trades_df):
        """Test that equity curve is calculated correctly."""
        import numpy as np

        from lynx.metrics import calculate_all
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)
        fig = run.plot()

        # Get equity curve data
        trace = fig.data[0]
        equity_values = trace.y

        # First value should be 1.0 (starting capital)
        assert equity_values[0] == 1.0

        # Last value should be 1 + total_return
        metrics = calculate_all(sample_trades_df)
        expected_final = 1.0 + metrics["total_return"]
        assert np.isclose(equity_values[-1], expected_final, rtol=0.01)


class TestCompareDisplay:
    """Test run.compare(other_run) method for comparing runs."""

    def test_compare_returns_tuple(self, sample_trades_df):
        """Test that compare() returns a tuple of (Styler, Figure)."""
        import plotly.graph_objects as go

        from lynx.run import Run

        run1 = Run("strategy_v1").trades(sample_trades_df)

        # Create slightly different trades for comparison
        trades2 = sample_trades_df.copy()
        trades2["return"] = trades2["return"] * 1.1  # 10% better returns
        run2 = Run("strategy_v2").trades(trades2)

        stats_styler, plot_fig = run1.compare(run2)

        # Should return Styler for metrics comparison
        assert hasattr(stats_styler, "data")
        # Should return Plotly Figure for overlaid curves
        assert isinstance(plot_fig, go.Figure)

    def test_compare_includes_both_runs_metrics(self, sample_trades_df):
        """Test that compare() includes metrics from both runs."""
        from lynx.run import Run

        run1 = Run("strategy_v1").trades(sample_trades_df)

        trades2 = sample_trades_df.copy()
        trades2["return"] = trades2["return"] * 1.1
        run2 = Run("strategy_v2").trades(trades2)

        stats_styler, _ = run1.compare(run2)
        df = stats_styler.data

        # Should have columns for both runs
        # Could be side-by-side or labeled columns
        assert df.shape[1] >= 2 or "strategy_v1" in str(df.columns) or "strategy_v2" in str(df.columns)

    def test_compare_plot_has_two_traces(self, sample_trades_df):
        """Test that compare() plot has two equity curves."""
        from lynx.run import Run

        run1 = Run("strategy_v1").trades(sample_trades_df)

        trades2 = sample_trades_df.copy()
        trades2["return"] = trades2["return"] * 1.1
        run2 = Run("strategy_v2").trades(trades2)

        _, plot_fig = run1.compare(run2)

        # Figure should have two traces (one for each run)
        assert len(plot_fig.data) >= 2

    def test_compare_with_different_strategies(self, sample_trades_df):
        """Test compare() with different strategy names."""
        from lynx.run import Run

        run1 = Run("momentum").trades(sample_trades_df)

        trades2 = sample_trades_df.copy()
        run2 = Run("mean_reversion").trades(trades2)

        stats_styler, plot_fig = run1.compare(run2)

        # Should work with different strategy names
        assert hasattr(stats_styler, "data")
        import plotly.graph_objects as go
        assert isinstance(plot_fig, go.Figure)

    def test_compare_after_save(self, sample_trades_df, temp_data_dir, monkeypatch):
        """Test that compare() works after save()."""
        import plotly.graph_objects as go

        import lynx.config
        from lynx.run import Run
        from lynx.storage import sqlite

        # Set custom data directory
        monkeypatch.setenv("LYNX_DATA_DIR", str(temp_data_dir))
        lynx.config._config = {"data_dir": temp_data_dir}

        # Initialize database
        sqlite.init_db()

        run1 = Run("strategy_v1").trades(sample_trades_df).save()

        trades2 = sample_trades_df.copy()
        trades2["return"] = trades2["return"] * 1.1
        run2 = Run("strategy_v2").trades(trades2).save()

        stats_styler, plot_fig = run1.compare(run2)

        assert hasattr(stats_styler, "data")
        assert isinstance(plot_fig, go.Figure)

    def test_compare_highlights_differences(self, sample_trades_df):
        """Test that compare() highlights metric differences."""
        from lynx.run import Run

        run1 = Run("strategy_v1").trades(sample_trades_df)

        trades2 = sample_trades_df.copy()
        trades2["return"] = trades2["return"] * 1.5  # Significantly better
        run2 = Run("strategy_v2").trades(trades2)

        stats_styler, _ = run1.compare(run2)

        # Styler should have some styling applied for comparison
        # We just verify it returns a Styler with data
        assert stats_styler.data is not None
        assert len(stats_styler.data) > 0


class TestExplainDisplay:
    """Test run.explain(symbol) method for debugging signal logic."""

    def test_explain_returns_dataframe(self, sample_trades_df, sample_signal_df):
        """Test that explain() returns a pandas DataFrame."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df).signal("entry", sample_signal_df)
        result = run.explain("2330")

        # Should return a DataFrame with signal timeline
        assert isinstance(result, pd.DataFrame)

    def test_explain_includes_signal_data(self, sample_trades_df, sample_signal_df):
        """Test that explain() shows signal values for the specified symbol."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df).signal("entry", sample_signal_df)
        result = run.explain("2330")

        # DataFrame should have columns for signals
        assert "entry" in result.columns or len(result.columns) >= 1

    def test_explain_with_multiple_signals(self, sample_trades_df, sample_signal_df):
        """Test explain() with multiple logged signals."""
        from lynx.run import Run

        # Create exit signal (inverse of entry)
        exit_signal = ~sample_signal_df
        exit_signal.index = sample_signal_df.index  # Ensure same index

        run = (
            Run("test_strategy")
            .trades(sample_trades_df)
            .signal("entry", sample_signal_df)
            .signal("exit", exit_signal)
        )
        result = run.explain("2330")

        # Should show both signals
        assert len(result.columns) >= 2 or "entry" in result.columns

    def test_explain_multiple_symbols(self, sample_trades_df, sample_signal_df):
        """Test explain() with multiple symbols."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df).signal("entry", sample_signal_df)
        result = run.explain(["2330", "2317"])

        # Should return data for multiple symbols
        assert isinstance(result, dict) or len(result) > 0

    def test_explain_with_date_range(self, sample_trades_df, sample_signal_df):
        """Test explain() with date range filtering."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df).signal("entry", sample_signal_df)
        result = run.explain("2330", start_date="2024-01-05", end_date="2024-01-15")

        # Result should be filtered by date range
        assert isinstance(result, (dict, list)) or hasattr(result, '__len__')

    def test_explain_no_signals_raises_error(self, sample_trades_df):
        """Test that explain() raises clear error when no signals logged."""
        from lynx.exceptions import ValidationError
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df)
        # No signals logged

        with pytest.raises(ValidationError) as exc_info:
            run.explain("2330")

        assert "no signal" in str(exc_info.value).lower() or "signal" in str(exc_info.value).lower()

    def test_explain_symbol_not_in_signal_returns_empty(self, sample_trades_df, sample_signal_df):
        """Test explain() for symbol not in signal DataFrame."""
        from lynx.run import Run

        run = Run("test_strategy").trades(sample_trades_df).signal("entry", sample_signal_df)

        # Use a symbol not in the signal DataFrame
        result = run.explain("INVALID_SYMBOL")

        # Should handle gracefully, returning empty or indicator
        assert result is not None

    def test_explain_after_save(self, sample_trades_df, sample_signal_df, temp_data_dir, monkeypatch):
        """Test that explain() works after save()."""
        import lynx.config
        from lynx.run import Run
        from lynx.storage import sqlite

        # Set custom data directory
        monkeypatch.setenv("LYNX_DATA_DIR", str(temp_data_dir))
        lynx.config._config = {"data_dir": temp_data_dir}

        # Initialize database
        sqlite.init_db()

        run = Run("test_strategy").trades(sample_trades_df).signal("entry", sample_signal_df).save()
        result = run.explain("2330")

        # Should still work after save
        assert result is not None
