"""Core backtest engine."""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Literal

import pandas as pd

if TYPE_CHECKING:
    from lynx.run import Run

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
        price: pd.DataFrame | None = None,
        initial_capital: float = 1_000_000,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        conflict_mode: ConflictMode = "exit_first",
        fees: dict[str, dict[str, float]] | None = None,
        lot_size: dict[str, int] | None = None,
        auto_fetch_prices: bool = True,
    ):
        """Initialize backtest engine.

        Args:
            entry_signal: Entry signal DataFrame (0-1 values)
            exit_signal: Exit signal DataFrame (0-1 values)
            price: Close price DataFrame (optional if auto_fetch_prices=True)
            initial_capital: Starting capital
            stop_loss: Stop loss percentage (e.g., 0.05 for 5%)
            take_profit: Take profit percentage (e.g., 0.10 for 10%)
            conflict_mode: How to handle entry/exit conflicts
            fees: Custom fee configuration
            lot_size: Custom lot size configuration
            auto_fetch_prices: Auto-fetch prices from Yahoo Finance if price is None
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
        self.auto_fetch_prices = auto_fetch_prices

        # State
        self.cash = initial_capital
        self.positions: dict[str, Position] = {}  # symbol -> Position
        self.trades: list[dict] = []
        self.equity_history: list[dict] = []

    def run(self) -> None:
        """Execute the backtest simulation."""
        from lynx.backtest.costs import calculate_buy_cost
        from lynx.backtest.defaults import get_fees_for_symbol, get_lot_size_for_symbol

        # Auto-fetch prices if needed
        if self.price is None and self.auto_fetch_prices:
            from lynx.data.cache import fetch_prices_with_cache
            from lynx.data.exceptions import InvalidSymbolError
            from lynx.data.yahoo import validate_symbols

            # Get symbols from entry signal columns
            symbols = list(self.entry_signal.columns)

            # Validate symbols
            validation = validate_symbols(symbols)
            if validation.invalid_symbols:
                raise InvalidSymbolError(
                    f"Cannot fetch from Yahoo Finance: {validation.invalid_symbols}"
                )

            # Get date range from signals
            start_date = min(
                self.entry_signal.index.min(),
                self.exit_signal.index.min(),
            )
            end_date = max(
                self.entry_signal.index.max(),
                self.exit_signal.index.max(),
            )

            # Convert to date if Timestamp
            if hasattr(start_date, 'date'):
                start_date = start_date.date()
            if hasattr(end_date, 'date'):
                end_date = end_date.date()

            # Fetch prices
            self.price = fetch_prices_with_cache(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
            )

        # Validate price is available
        if self.price is None:
            raise ValueError("price is required when auto_fetch_prices=False")

        symbols = list(self.price.columns)
        dates = self.price.index.tolist()

        # Align signals to price dates
        entry_aligned = self.entry_signal.reindex(dates).fillna(0)
        exit_aligned = self.exit_signal.reindex(dates).fillna(0)

        # Track positions marked for exit (for next day execution)
        pending_exits: dict[str, str] = {}  # symbol -> reason

        for _i, current_date in enumerate(dates):
            current_prices = self.price.loc[current_date]

            # Step 1: Execute pending exits (from previous day's stop/take profit)
            for symbol, reason in list(pending_exits.items()):
                if symbol in self.positions:
                    self._execute_exit(
                        symbol=symbol,
                        exit_date=current_date,
                        price=current_prices[symbol],
                        exit_ratio=1.0,
                        reason=reason,
                    )
            pending_exits.clear()

            # Step 2: Check stop loss / take profit at current prices
            for symbol, pos in list(self.positions.items()):
                current_price = current_prices[symbol]
                return_pct = pos.return_pct(current_price)

                if self.stop_loss and return_pct <= -self.stop_loss:
                    pending_exits[symbol] = "stop_loss"
                elif self.take_profit and return_pct >= self.take_profit:
                    pending_exits[symbol] = "take_profit"

            # Step 3: Process exit signals
            for symbol in symbols:
                exit_value = exit_aligned.loc[current_date, symbol]
                if exit_value > 0 and symbol in self.positions:
                    # Check for conflict
                    entry_value = entry_aligned.loc[current_date, symbol]
                    if entry_value > 0:
                        if self.conflict_mode == "entry_first":
                            continue  # Skip exit
                        elif self.conflict_mode == "ignore":
                            continue  # Skip both (entry handled later)

                    self._execute_exit(
                        symbol=symbol,
                        exit_date=current_date,
                        price=current_prices[symbol],
                        exit_ratio=exit_value,
                        reason="signal",
                    )

            # Step 4: Process entry signals
            entry_row = entry_aligned.loc[current_date]
            row_sum = entry_row.sum()

            if row_sum > 0:
                # Cap investment at 100% of cash
                invest_ratio = min(row_sum, 1.0)
                investable = self.cash * invest_ratio

                # Collect candidates for entry
                candidates = []
                for symbol in symbols:
                    signal_value = entry_row[symbol]
                    if signal_value <= 0:
                        continue

                    # Skip if already holding
                    if symbol in self.positions:
                        continue

                    # Check for conflict in ignore mode
                    exit_value = exit_aligned.loc[current_date, symbol]
                    if exit_value > 0 and self.conflict_mode == "ignore":
                        continue

                    candidates.append((symbol, signal_value))

                if candidates:
                    # Calculate initial allocations
                    candidate_sum = sum(sv for _, sv in candidates)
                    purchases = []

                    for symbol, signal_value in candidates:
                        weight = signal_value / candidate_sum
                        allocation = investable * weight

                        lot_size = get_lot_size_for_symbol(symbol, self.custom_lot_size)
                        fees = get_fees_for_symbol(symbol, self.custom_fees)
                        price = current_prices[symbol]

                        # Account for fees when calculating max shares
                        commission_rate = fees.get("commission_rate", 0.0)
                        commission_discount = fees.get("commission_discount", 1.0)
                        slippage = fees.get("slippage", 0.0)
                        effective_rate = 1 + commission_rate * commission_discount + slippage

                        max_shares = int(allocation / (price * effective_rate))
                        shares = (max_shares // lot_size) * lot_size

                        if shares > 0:
                            cost = calculate_buy_cost(price, shares, fees)
                            purchases.append({
                                "symbol": symbol,
                                "shares": shares,
                                "price": price,
                                "cost": cost,
                                "lot_size": lot_size,
                                "fees": fees,
                                "weight": weight,
                            })

                    # Check total cost and scale down if needed
                    total_cost = sum(p["cost"] for p in purchases)
                    if total_cost > self.cash and purchases:
                        scale = self.cash / total_cost * 0.99  # 1% safety margin
                        for p in purchases:
                            new_shares = int(p["shares"] * scale)
                            new_shares = (new_shares // p["lot_size"]) * p["lot_size"]
                            p["shares"] = new_shares
                            if new_shares > 0:
                                p["cost"] = calculate_buy_cost(p["price"], new_shares, p["fees"])
                            else:
                                p["cost"] = 0

                    # Execute purchases
                    for p in purchases:
                        if p["shares"] <= 0:
                            continue
                        if p["cost"] > self.cash:
                            continue

                        self.positions[p["symbol"]] = Position(
                            symbol=p["symbol"],
                            shares=p["shares"],
                            entry_price=p["price"],
                            entry_date=current_date.date() if hasattr(current_date, 'date') else current_date,
                            entry_cost=p["cost"],
                        )
                        self.cash -= p["cost"]

            # Step 5: Record daily equity
            holdings_value = sum(
                pos.current_value(current_prices[pos.symbol])
                for pos in self.positions.values()
            )
            equity = self.cash + holdings_value

            prev_equity = self.equity_history[-1]["equity"] if self.equity_history else self.initial_capital
            daily_return = (equity - prev_equity) / prev_equity if prev_equity > 0 else 0.0

            self.equity_history.append({
                "date": current_date,
                "equity": equity,
                "cash": self.cash,
                "holdings_value": holdings_value,
                "daily_return": daily_return,
            })

        # Close any remaining positions at last price
        last_date = dates[-1]
        last_prices = self.price.loc[last_date]
        for symbol in list(self.positions.keys()):
            self._execute_exit(
                symbol=symbol,
                exit_date=last_date,
                price=last_prices[symbol],
                exit_ratio=1.0,
                reason="end_of_data",
            )

    def _execute_exit(
        self,
        symbol: str,
        exit_date,
        price: float,
        exit_ratio: float,
        reason: str,
    ) -> None:
        """Execute an exit order."""
        from lynx.backtest.costs import calculate_sell_revenue
        from lynx.backtest.defaults import get_fees_for_symbol, get_lot_size_for_symbol

        pos = self.positions.get(symbol)
        if pos is None:
            return

        fees = get_fees_for_symbol(symbol, self.custom_fees)

        # Calculate shares to exit
        shares_to_exit = int(pos.shares * exit_ratio)
        if shares_to_exit <= 0:
            return

        # Get lot size for rounding
        lot_size = get_lot_size_for_symbol(symbol, self.custom_lot_size)

        # Round to lot size (for partial exits)
        if exit_ratio < 1.0:
            shares_to_exit = (shares_to_exit // lot_size) * lot_size
            if shares_to_exit <= 0:
                return

        actual_exited = pos.reduce(shares_to_exit)
        revenue = calculate_sell_revenue(price, actual_exited, fees)
        self.cash += revenue

        # Calculate return for this trade
        entry_cost_per_share = pos.entry_cost / (pos.shares + actual_exited)
        trade_cost = entry_cost_per_share * actual_exited
        trade_return = (revenue - trade_cost) / trade_cost

        # Record trade
        self.trades.append({
            "symbol": symbol,
            "entry_date": pos.entry_date,
            "exit_date": exit_date.date() if hasattr(exit_date, 'date') else exit_date,
            "entry_price": pos.entry_price,
            "exit_price": price,
            "shares": actual_exited,
            "return": trade_return,
            "exit_reason": reason,
        })

        # Remove position if fully exited
        if pos.shares <= 0:
            del self.positions[symbol]


def backtest(
    strategy_name: str,
    entry_signal: pd.DataFrame,
    exit_signal: pd.DataFrame,
    price: pd.DataFrame | None = None,
    initial_capital: float = 1_000_000,
    stop_loss: float | None = None,
    take_profit: float | None = None,
    conflict_mode: ConflictMode = "exit_first",
    fees: dict[str, dict[str, float]] | None = None,
    lot_size: dict[str, int] | None = None,
    auto_fetch_prices: bool = True,
) -> "Run":
    """Run a backtest and return a saved Run object.

    Args:
        strategy_name: Name for the strategy
        entry_signal: Entry signal DataFrame (0-1 values)
        exit_signal: Exit signal DataFrame (0-1 values)
        price: Close price DataFrame (optional if auto_fetch_prices=True)
        initial_capital: Starting capital (default: 1,000,000)
        stop_loss: Stop loss percentage (e.g., 0.05 for 5%)
        take_profit: Take profit percentage (e.g., 0.10 for 10%)
        conflict_mode: How to handle entry/exit conflicts
        fees: Custom fee configuration
        lot_size: Custom lot size configuration
        auto_fetch_prices: Auto-fetch prices from Yahoo Finance if price is None (default: True)

    Returns:
        Run object with trades, metrics, and equity curve saved

    Raises:
        ValidationError: If inputs are invalid
    """
    from lynx.backtest.validators import validate_backtest_inputs
    from lynx.run import Run
    from lynx.storage import sqlite

    # Validate inputs - only validate price if provided
    if price is not None:
        validate_backtest_inputs(entry_signal, exit_signal, price)

    # Initialize database
    sqlite.init_db()

    # Run backtest
    engine = BacktestEngine(
        entry_signal=entry_signal,
        exit_signal=exit_signal,
        price=price,
        initial_capital=initial_capital,
        stop_loss=stop_loss,
        take_profit=take_profit,
        conflict_mode=conflict_mode,
        fees=fees,
        lot_size=lot_size,
        auto_fetch_prices=auto_fetch_prices,
    )
    engine.run()

    # Create trades DataFrame
    trades_df = pd.DataFrame(engine.trades)

    # Handle empty trades case
    if trades_df.empty:
        trades_df = pd.DataFrame({
            "symbol": pd.Series([], dtype=str),
            "entry_date": pd.Series([], dtype="datetime64[ns]"),
            "exit_date": pd.Series([], dtype="datetime64[ns]"),
            "entry_price": pd.Series([], dtype=float),
            "exit_price": pd.Series([], dtype=float),
            "shares": pd.Series([], dtype=int),
            "return": pd.Series([], dtype=float),
            "exit_reason": pd.Series([], dtype=str),
        })
    else:
        # Convert dates to datetime
        trades_df["entry_date"] = pd.to_datetime(trades_df["entry_date"])
        trades_df["exit_date"] = pd.to_datetime(trades_df["exit_date"])

    # Create equity DataFrame
    equity_df = pd.DataFrame(engine.equity_history)
    if not equity_df.empty:
        equity_df = equity_df.set_index("date")

    # Build params dict
    params = {
        "initial_capital": initial_capital,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "conflict_mode": conflict_mode,
    }

    # Create and save Run
    run = Run(name=strategy_name, params=params)
    run.trades(trades_df)
    run.data("equity", equity_df)
    run.signal("entry_signal", entry_signal)
    run.signal("exit_signal", exit_signal)
    # Save price from engine (may have been auto-fetched)
    run.data("price", engine.price)
    run.save()

    return run
