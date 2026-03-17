#!/usr/bin/env python3
"""Backtest all strategies across instruments and timeframes."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtest.engine import run_backtest
from src.strategies import STRATEGIES

INSTRUMENTS = ["XAUUSD", "EURUSD"]
TIMEFRAMES = ["1h", "1d"]
PERIOD = "1y"

results = []

for strat_name in STRATEGIES:
    for inst in INSTRUMENTS:
        for tf in TIMEFRAMES:
            label = f"{strat_name:20s} | {inst:8s} | {tf:3s}"
            try:
                r = run_backtest(
                    strategy_name=strat_name,
                    instrument=inst,
                    period=PERIOD,
                    interval=tf,
                )
                results.append(r | {"timeframe": tf})
                print(f"✅ {label} | trades={r['total_trades']:3d} | ret={r['return_pct']:7.2f}% | wr={r['win_rate_pct']:5.1f}%")
            except Exception as e:
                print(f"❌ {label} | ERROR: {e}")
                results.append({
                    "strategy": strat_name, "instrument": inst, "timeframe": tf,
                    "return_pct": 0, "win_rate_pct": 0, "max_drawdown_pct": 0,
                    "profit_factor": 0, "total_trades": 0, "error": str(e),
                })

# Print summary table
print("\n" + "=" * 110)
print(f"{'Strategy':<20} {'Instrument':<10} {'TF':<4} {'Return%':>8} {'WinRate%':>9} {'MaxDD%':>8} {'PF':>6} {'Trades':>7}")
print("-" * 110)
for r in results:
    print(f"{r['strategy']:<20} {r['instrument']:<10} {r.get('timeframe','?'):<4} "
          f"{r['return_pct']:>8.2f} {r['win_rate_pct']:>9.1f} {r['max_drawdown_pct']:>8.2f} "
          f"{r.get('profit_factor',0):>6.2f} {r['total_trades']:>7d}")
print("=" * 110)
