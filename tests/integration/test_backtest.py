"""Integration tests for lynx.backtest()."""

import pandas as pd
import pytest

import lynx


@pytest.fixture
def backtest_data():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    entry_signal = pd.DataFrame({
        "2330.TW": [0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
        "2317.TW": [0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
    }, index=dates)
    exit_signal = pd.DataFrame({
        "2330.TW": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        "2317.TW": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    }, index=dates)
    price = pd.DataFrame({
        "2330.TW": [580.0, 585.0, 590.0, 600.0, 595.0, 600.0, 605.0, 610.0, 615.0, 620.0],
        "2317.TW": [112.0, 113.0, 114.0, 116.0, 115.0, 116.0, 117.0, 118.0, 119.0, 120.0],
    }, index=dates)
    return entry_signal, exit_signal, price


class TestLynxBacktest:
    def test_backtest_returns_run_object(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        assert run is not None
        assert run.id is not None
        assert run.strategy_name == "test_strategy"

    def test_backtest_calculates_metrics(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        assert "total_return" in run.metrics
        assert "sharpe_ratio" in run.metrics
        assert "max_drawdown" in run.metrics
        assert "num_trades" in run.metrics

    def test_backtest_saves_trades(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        trades = run.get_trades()
        assert len(trades) > 0
        assert "symbol" in trades.columns
        assert "entry_price" in trades.columns
        assert "exit_price" in trades.columns
        assert "shares" in trades.columns

    def test_backtest_saves_equity_curve(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        equity = run.get_data("equity")
        assert len(equity) == 10  # 10 trading days
        assert "equity" in equity.columns
        assert "cash" in equity.columns

    def test_backtest_can_be_loaded(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        # Load from storage
        loaded_run = lynx.load(run.id)
        assert loaded_run.id == run.id
        assert loaded_run.metrics["num_trades"] == run.metrics["num_trades"]

    def test_backtest_with_stop_loss(self, temp_data_dir):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        entry_signal = pd.DataFrame({
            "TEST.US": [1.0, 0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "TEST.US": [0.0, 0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        price = pd.DataFrame({
            "TEST.US": [100.0, 95.0, 88.0, 85.0, 80.0],
        }, index=dates)

        run = lynx.backtest(
            strategy_name="stop_loss_test",
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=price,
            initial_capital=10_000,
            stop_loss=0.10,
            fees={".US": {"commission_rate": 0.0, "slippage": 0.0}},
        )

        trades = run.get_trades()
        assert len(trades) == 1
        assert trades.iloc[0]["exit_reason"] == "stop_loss"

    def test_backtest_appears_in_runs_list(self, temp_data_dir, backtest_data):
        entry, exit_, price = backtest_data

        run = lynx.backtest(
            strategy_name="list_test_strategy",
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=10_000_000,
        )

        runs_list = lynx.runs(strategy="list_test_strategy")
        assert len(runs_list) == 1
        assert runs_list[0].id == run.id
