"""Test backtest engine with 2330.TW using 5-day moving average strategy.

This script demonstrates the auto-fetch feature of the backtest engine.
It uses a simple MA5 crossover strategy on TSMC stock (2330.TW).
"""

import pandas as pd
import yfinance as yf

import lynx


def create_ma5_signals(symbol: str, start_date: str, end_date: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create entry/exit signals based on 5-day moving average crossover.

    Strategy:
    - Entry: Price crosses above MA5 (bullish crossover)
    - Exit: Price crosses below MA5 (bearish crossover)

    Args:
        symbol: Stock symbol (e.g., "2330.TW")
        start_date: Start date in "YYYY-MM-DD" format
        end_date: End date in "YYYY-MM-DD" format

    Returns:
        Tuple of (entry_signal, exit_signal) DataFrames
    """
    # Fetch historical data
    ticker = yf.Ticker(symbol)
    hist = ticker.history(start=start_date, end=end_date)

    if hist.empty:
        raise ValueError(f"No data fetched for {symbol}")

    # Calculate 5-day moving average
    close = hist["Close"]
    ma5 = close.rolling(window=5).mean()

    # Generate signals
    # Entry: price crosses above MA5
    # Exit: price crosses below MA5
    above_ma = close > ma5
    prev_above_ma = above_ma.shift(1)
    prev_above_ma = prev_above_ma.where(prev_above_ma.notna(), False).astype(bool)
    entry_signal = above_ma & (~prev_above_ma)  # Cross above
    exit_signal = (~above_ma) & prev_above_ma   # Cross below

    # Convert to DataFrame format expected by backtest engine
    entry_df = pd.DataFrame({symbol: entry_signal.astype(float)}, index=hist.index)
    exit_df = pd.DataFrame({symbol: exit_signal.astype(float)}, index=hist.index)

    # Normalize index to date only (remove timezone)
    entry_df.index = entry_df.index.tz_localize(None)
    exit_df.index = exit_df.index.tz_localize(None)

    return entry_df, exit_df


def main():
    """Run the backtest test."""
    symbol = "2330.TW"
    start_date = "2024-01-01"
    end_date = "2024-12-31"

    print(f"Testing backtest engine with {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Strategy: 5-day Moving Average Crossover")
    print("-" * 50)

    # Create signals
    print("\n1. Creating MA5 signals...")
    entry_signal, exit_signal = create_ma5_signals(symbol, start_date, end_date)

    entry_count = entry_signal[symbol].sum()
    exit_count = exit_signal[symbol].sum()
    print(f"   Entry signals: {int(entry_count)}")
    print(f"   Exit signals: {int(exit_count)}")

    # Run backtest with auto-fetch prices
    print("\n2. Running backtest (auto-fetching prices from Yahoo Finance)...")
    run = lynx.backtest(
        strategy_name="MA5_2330TW",
        entry_signal=entry_signal,
        exit_signal=exit_signal,
        # price is omitted - will be auto-fetched
        initial_capital=1_000_000,
    )

    # Display results
    print("\n3. Results:")
    print(f"   Run ID: {run.id}")
    print(f"   Trades: {len(run._trades_df)}")

    # Show metrics
    print("\n4. Metrics:")
    metrics = run._metrics
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.4f}")
        else:
            print(f"   {key}: {value}")

    # Show trades summary
    if not run._trades_df.empty:
        print("\n5. Trades Summary:")
        trades = run._trades_df
        print(trades.to_string())

        # Calculate win rate
        wins = (trades["return"] > 0).sum()
        total = len(trades)
        win_rate = wins / total if total > 0 else 0
        print(f"\n   Win Rate: {win_rate:.2%} ({wins}/{total})")
    else:
        print("\n5. No trades executed")

    print("\n" + "=" * 50)
    print("Test completed successfully!")
    return run


if __name__ == "__main__":
    main()
