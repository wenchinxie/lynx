"""Core backtest engine."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd

ConflictMode = Literal["exit_first", "entry_first", "ignore"]


@dataclass
class Position:
    """Represents an open position."""

    symbol: str
    shares: int
    entry_price: float
    entry_date: date
    entry_cost: float

    def current_value(self, current_price: float) -> float:
        """Calculate current market value of position."""
        return self.shares * current_price

    def return_pct(self, current_price: float) -> float:
        """Calculate return percentage based on entry price."""
        return (current_price - self.entry_price) / self.entry_price

    def reduce(self, shares_to_exit: int) -> int:
        """Reduce position by given shares. Returns actual shares exited."""
        actual_exit = min(shares_to_exit, self.shares)
        self.shares -= actual_exit
        return actual_exit


class BacktestEngine:
    """Vectorized backtest engine."""

    def __init__(
        self,
        entry_signal: pd.DataFrame,
        exit_signal: pd.DataFrame,
        price: pd.DataFrame,
        initial_capital: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        conflict_mode: ConflictMode = "exit_first",
        fees: dict[str, dict[str, float]] | None = None,
        lot_size: dict[str, int] | None = None,
    ):
        """Initialize backtest engine.

        Args:
            entry_signal: Entry signal DataFrame (0-1 values)
            exit_signal: Exit signal DataFrame (0-1 values)
            price: Close price DataFrame
            initial_capital: Starting capital
            stop_loss: Stop loss percentage (e.g., 0.05 for 5%)
            take_profit: Take profit percentage (e.g., 0.10 for 10%)
            conflict_mode: How to handle entry/exit conflicts
            fees: Custom fee configuration
            lot_size: Custom lot size configuration
        """
        self.entry_signal = entry_signal
        self.exit_signal = exit_signal
        self.price = price
        self.initial_capital = initial_capital
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.conflict_mode = conflict_mode
        self.custom_fees = fees
        self.custom_lot_size = lot_size

        # State
        self.cash = initial_capital
        self.positions: dict[str, Position] = {}  # symbol -> Position
        self.trades: list[dict] = []
        self.equity_history: list[dict] = []
