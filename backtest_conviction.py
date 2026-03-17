"""Backtest conviction scoring strategies and compare with originals."""
from src.backtest.engine import run_backtest
from src.analysis.report import format_report

tests = [
    ("high_conviction", "XAUUSD", "1y"),
    ("high_conviction", "EURUSD", "1y"),
    ("filtered_london_breakout", "XAUUSD", "1y"),
    ("filtered_structure_break", "XAUUSD", "1y"),
    # Originals for comparison
    ("london_breakout", "XAUUSD", "1y"),
    ("structure_break", "XAUUSD", "1y"),
]

results = []
for strat, instrument, period in tests:
    print(f"\n{'='*60}")
    print(f"Running: {strat} on {instrument} ({period})")
    print('='*60)
    try:
        r = run_backtest(strat, instrument=instrument, period=period, interval="1h")
        results.append(r)
        print(format_report(r))
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback; traceback.print_exc()
        results.append({"strategy": strat, "instrument": instrument, "error": str(e)})

# Summary table
print("\n\n" + "="*100)
print(f"{'Strategy':<30} {'Instrument':<10} {'Return%':>8} {'MaxDD%':>8} {'Trades':>7} {'WinR%':>7} {'Sharpe':>7} {'PF':>7}")
print("-"*100)
for r in results:
    if 'error' in r:
        print(f"{r['strategy']:<30} {r['instrument']:<10} {'ERROR':>8}")
    else:
        print(f"{r['strategy']:<30} {r['instrument']:<10} {r['return_pct']:>8.1f} {r['max_drawdown_pct']:>8.1f} {r['total_trades']:>7} {r['win_rate_pct']:>7.1f} {r['sharpe_ratio']:>7.2f} {r['profit_factor']:>7.2f}")
print("="*100)
