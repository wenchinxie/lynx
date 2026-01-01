"""Core backtest engine."""

from dataclasses import dataclass
from datetime import date


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
