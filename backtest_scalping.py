"""Backtest all 3 scalping strategies on XAUUSD and EURUSD M15, then analyze top performer."""
import pandas as pd
import numpy as np
from src.backtest.engine import run_backtest
from src.analysis.report import format_report
from src.data.fetcher import fetch
from src import load_config
from backtesting import Backtest

# ── Run all 6 combos ──────────────────────────────────────────────
strategies = ["scalp_ema_momentum", "scalp_sr_quick", "scalp_breakout"]
instruments = ["XAUUSD", "EURUSD"]
interval = "15m"
period = "60d"  # yfinance max for 15m

results = []
all_trades = {}

for strat in strategies:
    for inst in instruments:
        label = f"{strat} / {inst}"
        print(f"\n{'='*60}\n  {label}\n{'='*60}")
        try:
            from src.strategies import STRATEGIES
            config = load_config()
            df = fetch(symbol=inst, period=period, interval=interval, config=config)
            strategy_cls = STRATEGIES[strat]
            bt = Backtest(df, strategy_cls, cash=100000, commission=0.0002, exclusive_orders=True)
            stats = bt.run()
            from src.analysis.report import generate_report
            r = generate_report(stats, strat, inst)
            results.append(r)
            print(format_report(r))
            # Save trades for analysis
            trades_df = stats.get("_trades", None)
            if trades_df is not None and len(trades_df) > 0:
                all_trades[label] = (trades_df, df)
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback; traceback.print_exc()
            results.append({"strategy": strat, "instrument": inst, "error": str(e)})

# ── Summary Table ──────────────────────────────────────────────────
print("\n\n" + "="*110)
print(f"{'Strategy':<25} {'Inst':<8} {'Ret%':>7} {'MaxDD%':>7} {'Trades':>6} {'WinR%':>6} {'Sharpe':>7} {'PF':>6} {'AvgR':>5}")
print("-"*110)
for r in results:
    if 'error' in r:
        print(f"{r['strategy']:<25} {r['instrument']:<8} {'ERR':>7}")
    else:
        print(f"{r['strategy']:<25} {r['instrument']:<8} {r['return_pct']:>7.1f} {r['max_drawdown_pct']:>7.1f} {r['total_trades']:>6} {r['win_rate_pct']:>6.1f} {r['sharpe_ratio']:>7.2f} {r['profit_factor']:>6.2f} {r.get('avg_r_multiple','?'):>5}")
print("="*110)

# ── Find top performer ────────────────────────────────────────────
valid = [r for r in results if 'error' not in r and r['total_trades'] > 0]
if not valid:
    print("\nNo valid results to analyze.")
    exit()

# Rank by Sharpe then return
top = max(valid, key=lambda x: (x['sharpe_ratio'], x['return_pct']))
top_label = f"{top['strategy']} / {top['instrument']}"
print(f"\n🏆 Top performer: {top_label}")

# ── Trade-level analysis ──────────────────────────────────────────
if top_label in all_trades:
    trades_df, price_df = all_trades[top_label]
    print(f"\n{'='*60}\n  Trade Analysis: {top_label}\n{'='*60}")

    # Add hour and day columns
    if hasattr(trades_df, 'EntryTime'):
        entry_times = pd.to_datetime(trades_df['EntryTime'])
    else:
        entry_times = pd.to_datetime(trades_df.index)

    trades_df = trades_df.copy()
    trades_df['Hour'] = entry_times.dt.hour.values
    trades_df['DayOfWeek'] = entry_times.dt.dayofweek.values
    day_names = {0:'Mon',1:'Tue',2:'Wed',3:'Thu',4:'Fri',5:'Sat',6:'Sun'}

    # PnL by hour
    print("\n📊 PnL by Hour:")
    by_hour = trades_df.groupby('Hour')['PnL'].agg(['sum','count','mean'])
    by_hour.columns = ['TotalPnL','Count','AvgPnL']
    print(by_hour.to_string())

    # PnL by day
    print("\n📊 PnL by Day:")
    by_day = trades_df.groupby('DayOfWeek')['PnL'].agg(['sum','count','mean'])
    by_day.index = [day_names.get(d, d) for d in by_day.index]
    by_day.columns = ['TotalPnL','Count','AvgPnL']
    print(by_day.to_string())

    # Win vs Loss analysis
    wins = trades_df[trades_df['PnL'] > 0]
    losses = trades_df[trades_df['PnL'] < 0]
    print(f"\n📊 Win/Loss Stats:")
    print(f"  Avg Win:  ${wins['PnL'].mean():.2f}" if len(wins) else "  No wins")
    print(f"  Avg Loss: ${losses['PnL'].mean():.2f}" if len(losses) else "  No losses")

    # Identify bad hours (negative total PnL)
    bad_hours = by_hour[by_hour['TotalPnL'] < 0].index.tolist()
    print(f"\n⚠️  Bad hours (negative PnL): {bad_hours}")

    # Identify bad days
    by_day_raw = trades_df.groupby('DayOfWeek')['PnL'].sum()
    bad_days = by_day_raw[by_day_raw < 0].index.tolist()
    bad_day_names = [day_names.get(d, d) for d in bad_days]
    print(f"⚠️  Bad days: {bad_day_names}")

    # ── Apply data-driven filters and re-backtest ──────────────────
    print(f"\n{'='*60}\n  Re-backtesting with filters\n{'='*60}")

    strat_name = top['strategy']
    inst_name = top['instrument']
    strategy_cls = STRATEGIES[strat_name]

    # Create filtered strategy subclass
    filtered_bad_hours = set(bad_hours)
    filtered_bad_days = set(bad_days)

    class FilteredScalpStrategy(strategy_cls):
        _bad_hours = filtered_bad_hours
        _bad_days = filtered_bad_days

        def _in_session(self):
            try:
                idx = self.data.index[-1]
                h = idx.hour
                dow = idx.weekday()
            except AttributeError:
                return False
            if h in self._bad_hours or dow in self._bad_days:
                return False
            return super()._in_session()

    config = load_config()
    df = fetch(symbol=inst_name, period=period, interval=interval, config=config)
    bt = Backtest(df, FilteredScalpStrategy, cash=100000, commission=0.0002, exclusive_orders=True)
    stats_filtered = bt.run()
    r_filtered = generate_report(stats_filtered, f"{strat_name}_filtered", inst_name)
    print(format_report(r_filtered))

    # Final comparison
    print(f"\n{'='*110}")
    print(f"{'Strategy':<30} {'Inst':<8} {'Ret%':>7} {'MaxDD%':>7} {'Trades':>6} {'WinR%':>6} {'Sharpe':>7} {'PF':>6}")
    print("-"*110)
    for r in results + [r_filtered]:
        if 'error' not in r and r['total_trades'] > 0:
            print(f"{r['strategy']:<30} {r['instrument']:<8} {r['return_pct']:>7.1f} {r['max_drawdown_pct']:>7.1f} {r['total_trades']:>6} {r['win_rate_pct']:>6.1f} {r['sharpe_ratio']:>7.2f} {r['profit_factor']:>6.2f}")
    print("="*110)
else:
    print(f"\nNo trade data available for {top_label}")
