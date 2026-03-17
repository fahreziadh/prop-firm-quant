#!/usr/bin/env python3
"""Backtest S/R Break & Retest strategy on multiple pairs + trade analysis."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.backtest.engine import run_backtest
from src.analysis.report import format_report
from backtesting import Backtest
from src.data.fetcher import fetch
from src.strategies import STRATEGIES
from src import load_config

PAIRS = ["XAUUSD", "EURUSD", "GBPUSD"]
STRATEGY = "sr_break_retest"
PERIOD = "1y"
INTERVAL = "1h"


def run_backtests():
    results = {}
    all_trades = {}
    config = load_config()
    strategy_cls = STRATEGIES[STRATEGY]
    strat_config = config.get("strategies", {}).get(STRATEGY, {})

    for pair in PAIRS:
        print(f"\n{'='*60}")
        print(f"  {STRATEGY} on {pair} {INTERVAL} {PERIOD}")
        print(f"{'='*60}")
        try:
            result = run_backtest(
                strategy_name=STRATEGY,
                instrument=pair,
                period=PERIOD,
                interval=INTERVAL,
            )
            print(format_report(result))
            results[pair] = result

            # Run again to get raw trades (backtesting.py stats object)
            df = fetch(symbol=pair, period=PERIOD, interval=INTERVAL, config=config)
            bt = Backtest(df, strategy_cls, cash=config["prop_firm"]["account_size"],
                         commission=config["backtest"]["commission"], exclusive_orders=True)
            stats = bt.run(**strat_config)
            trades_df = stats._trades.copy()
            if not trades_df.empty:
                all_trades[pair] = trades_df
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    return results, all_trades


def analyze_trades(all_trades):
    """Trade-level analysis: PnL by hour, day, ATR patterns."""
    for pair, trades in all_trades.items():
        print(f"\n{'='*60}")
        print(f"  TRADE ANALYSIS: {pair}")
        print(f"{'='*60}")

        if trades.empty:
            print("  No trades to analyze.")
            continue

        # Add time features
        if 'EntryTime' in trades.columns:
            trades['Hour'] = pd.to_datetime(trades['EntryTime']).dt.hour
            trades['DayOfWeek'] = pd.to_datetime(trades['EntryTime']).dt.day_name()
            trades['DOW'] = pd.to_datetime(trades['EntryTime']).dt.weekday
        elif 'EntryBar' in trades.columns:
            print("  (No EntryTime column, skipping time analysis)")
            continue

        pnl_col = 'PnL' if 'PnL' in trades.columns else 'ReturnPct' if 'ReturnPct' in trades.columns else None
        if pnl_col is None:
            print(f"  Available columns: {list(trades.columns)}")
            continue

        # PnL by hour
        print(f"\n  PnL by Hour:")
        print(f"  {'Hour':>4} {'Trades':>6} {'WinRate':>8} {'AvgPnL':>10} {'TotalPnL':>10}")
        by_hour = trades.groupby('Hour')[pnl_col].agg(['count', 'mean', 'sum'])
        wins_by_hour = trades[trades[pnl_col] > 0].groupby('Hour')[pnl_col].count()
        for hour in sorted(by_hour.index):
            row = by_hour.loc[hour]
            wr = (wins_by_hour.get(hour, 0) / row['count'] * 100) if row['count'] > 0 else 0
            print(f"  {hour:>4} {int(row['count']):>6} {wr:>7.1f}% {row['mean']:>10.2f} {row['sum']:>10.2f}")

        # PnL by day
        print(f"\n  PnL by Day of Week:")
        print(f"  {'Day':>10} {'Trades':>6} {'WinRate':>8} {'AvgPnL':>10} {'TotalPnL':>10}")
        by_dow = trades.groupby('DOW')[pnl_col].agg(['count', 'mean', 'sum'])
        wins_by_dow = trades[trades[pnl_col] > 0].groupby('DOW')[pnl_col].count()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for dow in sorted(by_dow.index):
            row = by_dow.loc[dow]
            wr = (wins_by_dow.get(dow, 0) / row['count'] * 100) if row['count'] > 0 else 0
            print(f"  {day_names[dow]:>10} {int(row['count']):>6} {wr:>7.1f}% {row['mean']:>10.2f} {row['sum']:>10.2f}")

        # Win vs Loss analysis
        wins = trades[trades[pnl_col] > 0]
        losses = trades[trades[pnl_col] <= 0]
        print(f"\n  Win/Loss Summary:")
        print(f"    Total trades: {len(trades)}")
        print(f"    Wins: {len(wins)} ({len(wins)/len(trades)*100:.1f}%)")
        print(f"    Losses: {len(losses)} ({len(losses)/len(trades)*100:.1f}%)")
        if len(wins) > 0:
            print(f"    Avg Win: {wins[pnl_col].mean():.2f}")
        if len(losses) > 0:
            print(f"    Avg Loss: {losses[pnl_col].mean():.2f}")
        if len(wins) > 0 and len(losses) > 0 and losses[pnl_col].mean() != 0:
            print(f"    Profit Factor: {abs(wins[pnl_col].sum() / losses[pnl_col].sum()):.2f}")

        # Duration analysis if available
        if 'Duration' in trades.columns:
            print(f"\n  Duration:")
            print(f"    Avg Win Duration: {wins['Duration'].mean() if len(wins) > 0 else 'N/A'}")
            print(f"    Avg Loss Duration: {losses['Duration'].mean() if len(losses) > 0 else 'N/A'}")


if __name__ == "__main__":
    results, all_trades = run_backtests()
    analyze_trades(all_trades)
