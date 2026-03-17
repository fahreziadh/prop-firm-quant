#!/usr/bin/env python3
"""Compare backtest results with and without news filter."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.backtest.engine import run_backtest
from src import load_config

def compare(strategy, instrument, period="1y"):
    config = load_config()
    
    # Without news filter
    config_off = {**config, "news_filter": {"enabled": False}}
    r_off = run_backtest(strategy, instrument=instrument, period=period, config=config_off)
    
    # With news filter
    config_on = {**config, "news_filter": {"enabled": True, "window_minutes": 60, "impact_levels": ["high"]}}
    r_on = run_backtest(strategy, instrument=instrument, period=period, config=config_on)
    
    print(f"\n{'='*60}")
    print(f"  {strategy} | {instrument} | {period}")
    print(f"{'='*60}")
    print(f"  {'Metric':<25} {'No Filter':>15} {'News Filter':>15}")
    print(f"  {'-'*55}")
    
    for key in ["total_return_pct", "win_rate", "total_trades", "max_drawdown_pct", "sharpe_ratio", "profit_factor"]:
        v_off = r_off.get(key, "N/A")
        v_on = r_on.get(key, "N/A")
        fmt = lambda v: f"{v:.2f}" if isinstance(v, (int, float)) else str(v)
        print(f"  {key:<25} {fmt(v_off):>15} {fmt(v_on):>15}")
    print()

if __name__ == "__main__":
    for strat in ["structure_break", "london_breakout"]:
        try:
            compare(strat, "XAUUSD", "1y")
        except Exception as e:
            print(f"  ERROR {strat}: {e}")
