"""Tests for backtest engine."""

from datetime import date

import pandas as pd
import pytest


class TestPosition:
    def test_create_position(self):
        from lynx.backtest.engine import Position

        pos = Position(
            symbol="2330.TW",
            shares=1000,
            entry_price=580.0,
            entry_date=date(2024, 1, 2),
            entry_cost=581000.0,
        )
        assert pos.symbol == "2330.TW"
        assert pos.shares == 1000
        assert pos.entry_price == 580.0
        assert pos.entry_cost == 581000.0

    def test_position_current_value(self):
        from lynx.backtest.engine import Position

        pos = Position(
            symbol="2330.TW",
            shares=1000,
            entry_price=580.0,
            entry_date=date(2024, 1, 2),
            entry_cost=581000.0,
        )
        assert pos.current_value(600.0) == 600000.0

    def test_position_return_pct(self):
        from lynx.backtest.engine import Position

        pos = Position(
            symbol="2330.TW",
            shares=1000,
            entry_price=580.0,
            entry_date=date(2024, 1, 2),
            entry_cost=581000.0,
        )
        # (600 - 580) / 580 = 0.0345
        assert pos.return_pct(600.0) == pytest.approx(0.0345, rel=0.01)

    def test_position_partial_exit(self):
        from lynx.backtest.engine import Position

        pos = Position(
            symbol="2330.TW",
            shares=1000,
            entry_price=580.0,
            entry_date=date(2024, 1, 2),
            entry_cost=581000.0,
        )
        exited_shares = pos.reduce(500)
        assert exited_shares == 500
        assert pos.shares == 500

    def test_position_full_exit(self):
        from lynx.backtest.engine import Position

        pos = Position(
            symbol="2330.TW",
            shares=1000,
            entry_price=580.0,
            entry_date=date(2024, 1, 2),
            entry_cost=581000.0,
        )
        exited_shares = pos.reduce(1000)
        assert exited_shares == 1000
        assert pos.shares == 0


class TestBacktestEngine:
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        entry_signal = pd.DataFrame({
            "2330.TW": [0.5, 0.0, 0.0, 0.0, 0.0],
            "2317.TW": [0.5, 0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "2330.TW": [0.0, 0.0, 0.0, 1.0, 0.0],
            "2317.TW": [0.0, 0.0, 0.0, 1.0, 0.0],
        }, index=dates)
        price = pd.DataFrame({
            "2330.TW": [580.0, 585.0, 590.0, 595.0, 600.0],
            "2317.TW": [112.0, 113.0, 114.0, 115.0, 116.0],
        }, index=dates)
        return entry_signal, exit_signal, price

    def test_engine_initialization(self, sample_data):
        from lynx.backtest.engine import BacktestEngine

        entry, exit_, price = sample_data
        engine = BacktestEngine(
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=1_000_000,
        )
        assert engine.initial_capital == 1_000_000
        assert engine.cash == 1_000_000
        assert len(engine.positions) == 0

    def test_engine_with_stop_loss(self, sample_data):
        from lynx.backtest.engine import BacktestEngine

        entry, exit_, price = sample_data
        engine = BacktestEngine(
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=1_000_000,
            stop_loss=0.05,
        )
        assert engine.stop_loss == 0.05

    def test_engine_with_take_profit(self, sample_data):
        from lynx.backtest.engine import BacktestEngine

        entry, exit_, price = sample_data
        engine = BacktestEngine(
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=1_000_000,
            take_profit=0.10,
        )
        assert engine.take_profit == 0.10

    def test_engine_run_simple_trade(self, sample_data):
        from lynx.backtest.engine import BacktestEngine

        entry, exit_, price = sample_data
        engine = BacktestEngine(
            entry_signal=entry,
            exit_signal=exit_,
            price=price,
            initial_capital=1_000_000,
        )
        engine.run()

        # Should have executed trades
        assert len(engine.trades) > 0

        # Should have equity history for each day
        assert len(engine.equity_history) == 5

    def test_engine_generates_correct_trades(self):
        from lynx.backtest.engine import BacktestEngine

        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        entry_signal = pd.DataFrame({
            "TEST.US": [1.0, 0.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "TEST.US": [0.0, 0.0, 1.0],
        }, index=dates)
        price = pd.DataFrame({
            "TEST.US": [100.0, 110.0, 120.0],
        }, index=dates)

        # Use zero-fee config for precise test
        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=price,
            initial_capital=10_000,
            fees={".US": {"commission_rate": 0.0, "slippage": 0.0}},
        )
        engine.run()

        assert len(engine.trades) == 1
        trade = engine.trades[0]
        assert trade["symbol"] == "TEST.US"
        assert trade["entry_price"] == 100.0
        assert trade["exit_price"] == 120.0
        assert trade["exit_reason"] == "signal"

    def test_engine_respects_lot_size(self):
        from lynx.backtest.engine import BacktestEngine

        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        entry_signal = pd.DataFrame({
            "2330.TW": [1.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "2330.TW": [0.0, 1.0],
        }, index=dates)
        price = pd.DataFrame({
            "2330.TW": [580.0, 600.0],
        }, index=dates)

        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=price,
            initial_capital=1_000_000,
        )
        engine.run()

        # TW stocks must be bought in lots of 1000
        trade = engine.trades[0]
        assert trade["shares"] % 1000 == 0

    def test_engine_stop_loss_triggers(self):
        from lynx.backtest.engine import BacktestEngine

        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        entry_signal = pd.DataFrame({
            "TEST.US": [1.0, 0.0, 0.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "TEST.US": [0.0, 0.0, 0.0, 0.0],  # No exit signal
        }, index=dates)
        price = pd.DataFrame({
            "TEST.US": [100.0, 95.0, 90.0, 85.0],  # Price drops 15%
        }, index=dates)

        # Use zero-fee config for precise test
        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=price,
            initial_capital=10_000,
            stop_loss=0.10,  # 10% stop loss
            fees={".US": {"commission_rate": 0.0, "slippage": 0.0}},
        )
        engine.run()

        # Should have exited due to stop loss
        assert len(engine.trades) == 1
        assert engine.trades[0]["exit_reason"] == "stop_loss"

    def test_engine_take_profit_triggers(self):
        from lynx.backtest.engine import BacktestEngine

        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        entry_signal = pd.DataFrame({
            "TEST.US": [1.0, 0.0, 0.0, 0.0],
        }, index=dates)
        exit_signal = pd.DataFrame({
            "TEST.US": [0.0, 0.0, 0.0, 0.0],
        }, index=dates)
        price = pd.DataFrame({
            "TEST.US": [100.0, 105.0, 112.0, 115.0],  # Price rises 15%
        }, index=dates)

        # Use zero-fee config for precise test
        engine = BacktestEngine(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            price=price,
            initial_capital=10_000,
            take_profit=0.10,  # 10% take profit
            fees={".US": {"commission_rate": 0.0, "slippage": 0.0}},
        )
        engine.run()

        assert len(engine.trades) == 1
        assert engine.trades[0]["exit_reason"] == "take_profit"
