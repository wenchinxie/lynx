#!/usr/bin/env python3
"""Generate diverse test strategy data for Lynx dashboard testing."""

import sys
sys.path.insert(0, '/home/hanson/lynx/src')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import lynx


def generate_trades(
    symbols: list[str],
    start_date: str,
    end_date: str,
    num_trades: int,
    avg_return: float = 0.02,
    return_std: float = 0.05,
    avg_duration_days: int = 5,
) -> pd.DataFrame:
    """Generate realistic trading data."""

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    date_range = (end - start).days

    trades = []
    for _ in range(num_trades):
        symbol = random.choice(symbols)

        # Random entry date within range
        entry_offset = random.randint(0, max(0, date_range - avg_duration_days * 2))
        entry_date = start + timedelta(days=entry_offset)

        # Duration varies around average
        duration = max(1, int(np.random.exponential(avg_duration_days)))
        exit_date = entry_date + timedelta(days=duration)
        if exit_date > end:
            exit_date = end

        # Generate realistic prices
        base_prices = {
            '2330': 580,  # TSMC
            '2317': 45,   # Hon Hai
            '2454': 125,  # MediaTek
            '2412': 120,  # Chunghwa Telecom
            '2308': 25,   # Delta Electronics
            '2881': 55,   # Fubon Financial
            '2882': 42,   # Cathay Financial
            '2303': 35,   # UMC
            '3008': 90,   # Largan
            '2886': 28,   # Mega Financial
        }
        base_price = base_prices.get(symbol, 100)
        entry_price = base_price * (1 + np.random.uniform(-0.1, 0.1))

        # Generate return with some bias
        trade_return = np.random.normal(avg_return, return_std)
        trade_return = max(-0.5, min(0.5, trade_return))  # Cap extreme values

        exit_price = entry_price * (1 + trade_return)

        trades.append({
            'symbol': symbol,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': round(entry_price, 2),
            'exit_price': round(exit_price, 2),
            'return': round(trade_return, 4),
        })

    df = pd.DataFrame(trades)
    df = df.sort_values('entry_date').reset_index(drop=True)
    return df


def generate_signal_data(
    symbols: list[str],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Generate random signal data."""
    dates = pd.date_range(start_date, end_date, freq='D')
    data = {}
    for symbol in symbols:
        # Generate sparse signals (about 10% True)
        data[symbol] = np.random.choice([True, False], size=len(dates), p=[0.1, 0.9])
    return pd.DataFrame(data, index=dates)


def main():
    """Generate multiple test strategies with varied characteristics."""

    symbols_tw = ['2330', '2317', '2454', '2412', '2308', '2881', '2882', '2303', '3008', '2886']

    strategies = [
        # Strategy 1: Momentum - High frequency, moderate returns
        {
            'name': 'momentum_breakout',
            'params': {'lookback': 20, 'threshold': 0.02, 'stop_loss': 0.05},
            'tags': ['momentum', 'technical', 'tw-stock'],
            'notes': 'Momentum breakout strategy focusing on Taiwan tech stocks',
            'start': '2024-01-01',
            'end': '2024-06-30',
            'num_trades': 45,
            'avg_return': 0.025,
            'return_std': 0.04,
            'avg_duration': 3,
        },
        # Strategy 2: Mean Reversion - Lower frequency, higher win rate
        {
            'name': 'mean_reversion_rsi',
            'params': {'rsi_period': 14, 'oversold': 30, 'overbought': 70},
            'tags': ['mean-reversion', 'rsi', 'tw-stock'],
            'notes': 'RSI-based mean reversion strategy',
            'start': '2024-01-01',
            'end': '2024-06-30',
            'num_trades': 28,
            'avg_return': 0.018,
            'return_std': 0.03,
            'avg_duration': 7,
        },
        # Strategy 3: Value Investing - Long holding periods
        {
            'name': 'value_dividend',
            'params': {'min_yield': 0.04, 'pe_max': 15, 'holding_days': 30},
            'tags': ['value', 'dividend', 'long-term'],
            'notes': 'Dividend-focused value strategy for stable returns',
            'start': '2024-01-01',
            'end': '2024-06-30',
            'num_trades': 12,
            'avg_return': 0.035,
            'return_std': 0.025,
            'avg_duration': 25,
        },
        # Strategy 4: Pairs Trading
        {
            'name': 'pairs_tsmc_umc',
            'params': {'zscore_entry': 2.0, 'zscore_exit': 0.5, 'lookback': 60},
            'tags': ['pairs', 'statistical-arbitrage', 'semiconductor'],
            'notes': 'Statistical arbitrage between TSMC and UMC',
            'start': '2024-02-01',
            'end': '2024-06-30',
            'num_trades': 18,
            'avg_return': 0.012,
            'return_std': 0.02,
            'avg_duration': 5,
        },
        # Strategy 5: Trend Following - Longer trades
        {
            'name': 'trend_ma_crossover',
            'params': {'fast_ma': 10, 'slow_ma': 50, 'atr_multiplier': 2},
            'tags': ['trend', 'moving-average', 'tw-stock'],
            'notes': 'MA crossover trend following strategy',
            'start': '2024-01-01',
            'end': '2024-06-30',
            'num_trades': 22,
            'avg_return': 0.032,
            'return_std': 0.06,
            'avg_duration': 12,
        },
        # Strategy 6: Volatility Breakout
        {
            'name': 'volatility_breakout',
            'params': {'k': 0.5, 'atr_period': 20},
            'tags': ['volatility', 'breakout', 'intraday'],
            'notes': 'Larry Williams volatility breakout adapted for TW market',
            'start': '2024-03-01',
            'end': '2024-06-30',
            'num_trades': 55,
            'avg_return': 0.015,
            'return_std': 0.035,
            'avg_duration': 2,
        },
        # Strategy 7: Sector Rotation
        {
            'name': 'sector_rotation_financial',
            'params': {'rotation_period': 20, 'top_n': 3},
            'tags': ['sector', 'rotation', 'financial'],
            'notes': 'Sector rotation focusing on TW financial stocks',
            'start': '2024-01-01',
            'end': '2024-06-30',
            'num_trades': 15,
            'avg_return': 0.022,
            'return_std': 0.028,
            'avg_duration': 20,
        },
        # Strategy 8: High-Frequency Scalping
        {
            'name': 'scalping_orderflow',
            'params': {'tick_threshold': 5, 'profit_target': 0.003, 'max_hold_mins': 30},
            'tags': ['scalping', 'high-frequency', 'orderflow'],
            'notes': 'Order flow based scalping strategy',
            'start': '2024-04-01',
            'end': '2024-06-30',
            'num_trades': 120,
            'avg_return': 0.004,
            'return_std': 0.008,
            'avg_duration': 1,
        },
        # Strategy 9: Options-based (simulated as stock trades)
        {
            'name': 'covered_call_premium',
            'params': {'delta': 0.3, 'dte': 30, 'roll_trigger': 0.1},
            'tags': ['options', 'income', 'covered-call'],
            'notes': 'Covered call premium harvesting on high-IV stocks',
            'start': '2024-01-01',
            'end': '2024-06-30',
            'num_trades': 24,
            'avg_return': 0.02,
            'return_std': 0.015,
            'avg_duration': 28,
        },
        # Strategy 10: Machine Learning Signal
        {
            'name': 'ml_ensemble_signal',
            'params': {'model_type': 'xgboost', 'features': 42, 'threshold': 0.65},
            'tags': ['machine-learning', 'ensemble', 'quantitative'],
            'notes': 'XGBoost ensemble model with technical and fundamental features',
            'start': '2024-02-01',
            'end': '2024-06-30',
            'num_trades': 35,
            'avg_return': 0.028,
            'return_std': 0.045,
            'avg_duration': 8,
        },
    ]

    print("Generating test strategy data...")
    print("=" * 60)

    for i, strategy in enumerate(strategies, 1):
        print(f"\n[{i}/{len(strategies)}] Creating strategy: {strategy['name']}")

        # Select appropriate symbols
        if 'financial' in strategy.get('tags', []):
            symbols = ['2881', '2882', '2886']
        elif 'semiconductor' in strategy.get('tags', []):
            symbols = ['2330', '2303', '2454']
        else:
            symbols = symbols_tw[:6]  # Use first 6 symbols

        # Generate trades
        trades = generate_trades(
            symbols=symbols,
            start_date=strategy['start'],
            end_date=strategy['end'],
            num_trades=strategy['num_trades'],
            avg_return=strategy['avg_return'],
            return_std=strategy['return_std'],
            avg_duration_days=strategy['avg_duration'],
        )

        # Generate signal data
        signals = generate_signal_data(
            symbols=symbols,
            start_date=strategy['start'],
            end_date=strategy['end'],
        )

        # Log the run
        run = lynx.log(
            strategy['name'],
            trades=trades,
            params=strategy['params'],
            tags=strategy['tags'],
            notes=strategy['notes'],
            entry_signal=signals,
        )

        print(f"   Run ID: {run.id}")
        print(f"   Trades: {strategy['num_trades']}")
        print(f"   Total Return: {run.metrics.get('total_return', 0):.2%}")
        print(f"   Sharpe Ratio: {run.metrics.get('sharpe_ratio', 0):.2f}")
        print(f"   Win Rate: {run.metrics.get('win_rate', 0):.1%}")

    print("\n" + "=" * 60)
    print("Test data generation complete!")

    # Show summary of all runs
    print("\n📊 All available runs:")
    runs = lynx.runs(limit=20)
    for run in runs:
        print(f"  - {run.strategy_name}: {run.id}")


if __name__ == '__main__':
    main()
