"""Backtest Session Open Momentum Scalping strategy with full analysis."""
import pandas as pd
import numpy as np
from src.data.fetcher import fetch
from src.analysis.report import generate_report, format_report
from src.strategies import STRATEGIES
from src import load_config
from backtesting import Backtest

config = load_config()
instruments = ["XAUUSD", "EURUSD"]
interval = "15m"
period = "60d"
strat_name = "scalp_session_momentum"
strategy_cls = STRATEGIES[strat_name]

results = []
all_trades = {}

# Also run scalp_breakout for comparison
compare_strats = ["scalp_session_momentum", "scalp_breakout"]

for strat in compare_strats:
    cls = STRATEGIES[strat]
    for inst in instruments:
        label = f"{strat} / {inst}"
        print(f"\n{'='*60}\n  {label}\n{'='*60}")
        try:
            df = fetch(symbol=inst, period=period, interval=interval, config=config)
            bt = Backtest(df, cls, cash=100000, commission=0.0002, exclusive_orders=True)
            stats = bt.run()
            r = generate_report(stats, strat, inst)
            results.append(r)
            print(format_report(r))
            trades_df = stats.get("_trades", None)
            if trades_df is not None and len(trades_df) > 0:
                all_trades[label] = (trades_df, df)
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback; traceback.print_exc()
            results.append({"strategy": strat, "instrument": inst, "error": str(e)})

# ── Summary Table ──────────────────────────────────────────────────
print(f"\n\n{'='*110}")
print(f"{'Strategy':<30} {'Inst':<8} {'Ret%':>7} {'MaxDD%':>7} {'Trades':>6} {'WinR%':>6} {'Sharpe':>7} {'PF':>6} {'AvgR':>5}")
print("-"*110)
for r in results:
    if 'error' in r:
        print(f"{r['strategy']:<30} {r['instrument']:<8} {'ERR':>7}")
    else:
        print(f"{r['strategy']:<30} {r['instrument']:<8} {r['return_pct']:>7.1f} {r['max_drawdown_pct']:>7.1f} {r['total_trades']:>6} {r['win_rate_pct']:>6.1f} {r['sharpe_ratio']:>7.2f} {r['profit_factor']:>6.2f} {r.get('avg_r_multiple','?'):>5}")
print("="*110)

# ── Detailed Trade Analysis for session_momentum ──────────────────
for inst in instruments:
    label = f"scalp_session_momentum / {inst}"
    if label not in all_trades:
        print(f"\n⚠️  No trades for {label}")
        continue

    trades_df, price_df = all_trades[label]
    print(f"\n{'='*60}\n  Trade Analysis: {label}\n{'='*60}")

    trades_df = trades_df.copy()
    if hasattr(trades_df, 'EntryTime'):
        entry_times = pd.to_datetime(trades_df['EntryTime'])
    else:
        entry_times = pd.to_datetime(trades_df.index)

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

    # Win vs Loss
    wins = trades_df[trades_df['PnL'] > 0]
    losses = trades_df[trades_df['PnL'] < 0]
    print(f"\n📊 Win/Loss Stats:")
    print(f"  Avg Win:  ${wins['PnL'].mean():.2f}" if len(wins) else "  No wins")
    print(f"  Avg Loss: ${losses['PnL'].mean():.2f}" if len(losses) else "  No losses")
    if len(wins) and len(losses):
        print(f"  R-Multiple: {abs(wins['PnL'].mean() / losses['PnL'].mean()):.2f}")

    # ATR at entry - win vs loss
    print("\n📊 ATR at Entry (Win vs Loss):")
    # Approximate: get ATR values from price data at entry times
    from src.indicators.technical import atr_from_cols as _atr_fn
    atr_series = pd.Series(
        _atr_fn(price_df['High'].values, price_df['Low'].values, price_df['Close'].values, 14),
        index=price_df.index
    )
    for _, t in trades_df.iterrows():
        et = pd.to_datetime(t.get('EntryTime', t.name))
        # Find nearest ATR
        idx_loc = atr_series.index.get_indexer([et], method='nearest')[0]
        trades_df.loc[t.name if hasattr(t, 'name') else _, 'ATR_at_entry'] = atr_series.iloc[idx_loc]

    if 'ATR_at_entry' in trades_df.columns:
        win_atr = trades_df[trades_df['PnL'] > 0]['ATR_at_entry'].mean()
        loss_atr = trades_df[trades_df['PnL'] < 0]['ATR_at_entry'].mean()
        print(f"  Avg ATR (wins):   {win_atr:.4f}" if not np.isnan(win_atr) else "  N/A")
        print(f"  Avg ATR (losses): {loss_atr:.4f}" if not np.isnan(loss_atr) else "  N/A")

    # Momentum candle size win vs loss
    print("\n📊 Momentum Candle Size (Win vs Loss):")
    for _, t in trades_df.iterrows():
        et = pd.to_datetime(t.get('EntryTime', t.name))
        idx_loc = price_df.index.get_indexer([et], method='nearest')[0]
        body = abs(price_df['Close'].iloc[idx_loc] - price_df['Open'].iloc[idx_loc])
        trades_df.loc[t.name if hasattr(t, 'name') else _, 'MomentumBody'] = body

    if 'MomentumBody' in trades_df.columns:
        win_body = trades_df[trades_df['PnL'] > 0]['MomentumBody'].mean()
        loss_body = trades_df[trades_df['PnL'] < 0]['MomentumBody'].mean()
        print(f"  Avg Body (wins):   {win_body:.4f}" if not np.isnan(win_body) else "  N/A")
        print(f"  Avg Body (losses): {loss_body:.4f}" if not np.isnan(loss_body) else "  N/A")

    # Identify bad patterns
    bad_hours = by_hour[by_hour['TotalPnL'] < 0].index.tolist() if len(by_hour) else []
    by_day_raw = trades_df.groupby('DayOfWeek')['PnL'].sum()
    bad_days = by_day_raw[by_day_raw < 0].index.tolist()
    bad_day_names = [day_names.get(d, d) for d in bad_days]
    print(f"\n⚠️  Bad hours: {bad_hours}")
    print(f"⚠️  Bad days: {bad_day_names}")

# ── Data-driven filtered re-backtest ──────────────────────────────
print(f"\n\n{'='*60}\n  DATA-DRIVEN FILTERED RE-BACKTEST\n{'='*60}")

for inst in instruments:
    label = f"scalp_session_momentum / {inst}"
    if label not in all_trades:
        continue

    trades_df, _ = all_trades[label]
    trades_df = trades_df.copy()
    if hasattr(trades_df, 'EntryTime'):
        entry_times = pd.to_datetime(trades_df['EntryTime'])
    else:
        entry_times = pd.to_datetime(trades_df.index)
    trades_df['Hour'] = entry_times.dt.hour.values
    trades_df['DayOfWeek'] = entry_times.dt.dayofweek.values

    by_hour = trades_df.groupby('Hour')['PnL'].sum()
    bad_hours = set(by_hour[by_hour < 0].index.tolist())
    by_day = trades_df.groupby('DayOfWeek')['PnL'].sum()
    bad_days = set(by_day[by_day < 0].index.tolist())

    if not bad_hours and not bad_days:
        print(f"\n  {inst}: No bad patterns found, skipping filtered retest")
        continue

    print(f"\n  {inst}: Filtering out hours={bad_hours}, days={bad_days}")

    class FilteredSessionMomentum(strategy_cls):
        _bad_hours = bad_hours
        _bad_days = bad_days

        def next(self):
            try:
                idx = self.data.index[-1]
                if idx.hour in self._bad_hours or idx.weekday() in self._bad_days:
                    return
            except AttributeError:
                pass
            super().next()

    df = fetch(symbol=inst, period=period, interval=interval, config=config)
    bt = Backtest(df, FilteredSessionMomentum, cash=100000, commission=0.0002, exclusive_orders=True)
    stats = bt.run()
    r = generate_report(stats, f"session_momentum_filtered", inst)
    results.append(r)
    print(format_report(r))

# ── Final Comparison ──────────────────────────────────────────────
print(f"\n\n{'='*110}")
print(f"  FINAL COMPARISON - ALL STRATEGIES")
print(f"{'='*110}")
print(f"{'Strategy':<35} {'Inst':<8} {'Ret%':>7} {'MaxDD%':>7} {'Trades':>6} {'WinR%':>6} {'Sharpe':>7} {'PF':>6}")
print("-"*110)
for r in results:
    if 'error' not in r and r['total_trades'] > 0:
        print(f"{r['strategy']:<35} {r['instrument']:<8} {r['return_pct']:>7.1f} {r['max_drawdown_pct']:>7.1f} {r['total_trades']:>6} {r['win_rate_pct']:>6.1f} {r['sharpe_ratio']:>7.2f} {r['profit_factor']:>6.2f}")
    elif 'error' not in r:
        print(f"{r['strategy']:<35} {r['instrument']:<8} {'NO TRADES':>7}")
print("="*110)

# ── Test different RR ratios ──────────────────────────────────────
print(f"\n\n{'='*60}\n  RR RATIO SENSITIVITY TEST\n{'='*60}")
for rr in [1.0, 1.5, 2.0]:
    for inst in instruments:
        df = fetch(symbol=inst, period=period, interval=interval, config=config)
        bt = Backtest(df, strategy_cls, cash=100000, commission=0.0002, exclusive_orders=True)
        stats = bt.run(tp_rr=rr)
        r = generate_report(stats, f"session_mom_RR{rr}", inst)
        trades = r['total_trades']
        wr = r['win_rate_pct']
        ret = r['return_pct']
        pf = r['profit_factor']
        print(f"  RR={rr:.1f} | {inst:<8} | Trades={trades:>3} | WR={wr:>5.1f}% | Ret={ret:>6.1f}% | PF={pf:>5.2f}")
