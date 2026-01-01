"""Tests for backtest engine."""

import pandas as pd
import pytest
from datetime import date


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
