#!/usr/bin/env python3
"""Run all strategy backtests across instruments."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtest.engine import run_backtest
from src.strategies import STRATEGIES

strategies = list(STRATEGIES.keys())
instruments = ["XAUUSD", "EURUSD"]
period = "1y"
interval = "1h"

results = []
for instrument in instruments:
    for strat in strategies:
        print(f"\n{'='*60}")
        print(f"Running {strat} on {instrument} {interval} {period}...")
        try:
            r = run_backtest(strategy_name=strat, instrument=instrument, period=period, interval=interval)
            results.append({
                "strategy": strat,
                "instrument": instrument,
                "return_pct": r.get("return_pct", 0),
                "trades": r.get("total_trades", 0),
                "win_rate": r.get("win_rate", 0),
                "max_dd": r.get("max_drawdown_pct", 0),
                "sharpe": r.get("sharpe_ratio", 0),
                "profit_factor": r.get("profit_factor", 0),
            })
            print(f"  Return: {r.get('return_pct', 0):.2f}% | Trades: {r.get('total_trades', 0)} | WR: {r.get('win_rate', 0):.1f}% | MaxDD: {r.get('max_drawdown_pct', 0):.2f}% | Sharpe: {r.get('sharpe_ratio', 0):.2f}")
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"strategy": strat, "instrument": instrument, "return_pct": 0, "trades": 0, "win_rate": 0, "max_dd": 0, "sharpe": 0, "profit_factor": 0})

print(f"\n\n{'='*100}")
print(f"{'STRATEGY OPTIMIZATION RESULTS':^100}")
print(f"{'='*100}")
print(f"{'Strategy':<20} {'Instrument':<10} {'Return%':>9} {'Trades':>7} {'WinRate%':>9} {'MaxDD%':>8} {'Sharpe':>8} {'PF':>8}")
print(f"{'-'*100}")
for r in results:
    print(f"{r['strategy']:<20} {r['instrument']:<10} {r['return_pct']:>8.2f}% {r['trades']:>7} {r['win_rate']:>8.1f}% {r['max_dd']:>7.2f}% {r['sharpe']:>8.2f} {r['profit_factor']:>8.2f}")
print(f"{'='*100}")
