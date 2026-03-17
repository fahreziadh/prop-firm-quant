#!/usr/bin/env python3
"""Analyze trades by hour, day, and ATR for a given strategy+instrument."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from backtesting import Backtest
from src import load_config
from src.data.fetcher import fetch
from src.strategies import STRATEGIES
from src.indicators.technical import atr_from_cols


def analyze(strategy_name, instrument, period="1y", interval="1h"):
    config = load_config()
    # Temporarily remove data-driven filters for raw analysis
    strategy_cls = STRATEGIES[strategy_name]
    
    df = fetch(symbol=instrument, period=period, interval=interval, config=config)
    cash = config["prop_firm"]["account_size"]
    commission = config["backtest"]["commission"]
    
    params = config.get("strategies", {}).get(strategy_name, {})
    
    # Override filters to get raw trades for analysis
    override = dict(params)
    if hasattr(strategy_cls, 'atr_max'):
        override['atr_max'] = 0
    if hasattr(strategy_cls, 'atr_min'):
        override['atr_min'] = 0
    if hasattr(strategy_cls, 'skip_hours'):
        override['skip_hours'] = set()
    if hasattr(strategy_cls, 'focus_hours'):
        override['focus_hours'] = set()
    if hasattr(strategy_cls, 'skip_weekdays'):
        override['skip_weekdays'] = set()
    
    bt = Backtest(df, strategy_cls, cash=cash, commission=commission, exclusive_orders=True)
    stats = bt.run(**override)
    
    trades = stats._trades
    if trades is None or len(trades) == 0:
        print(f"No trades for {strategy_name} {instrument}")
        return
    
    # Compute ATR for each trade entry
    atr_vals = atr_from_cols(df.High.values, df.Low.values, df.Close.values, 14)
    
    results = []
    for _, t in trades.iterrows():
        entry_time = t['EntryTime']
        pnl = t['PnL']
        try:
            hour = entry_time.hour
            dow = entry_time.weekday()
        except:
            continue
        # Find ATR at entry
        idx_pos = df.index.get_indexer([entry_time], method='ffill')[0]
        atr_at_entry = atr_vals[idx_pos] if 0 <= idx_pos < len(atr_vals) else np.nan
        results.append({'hour': hour, 'dow': dow, 'pnl': pnl, 'atr': atr_at_entry, 'win': pnl > 0})
    
    rdf = pd.DataFrame(results)
    
    print(f"\n{'='*60}")
    print(f"TRADE ANALYSIS: {strategy_name} on {instrument} ({interval}, {period})")
    print(f"{'='*60}")
    print(f"Total trades: {len(rdf)}")
    
    # PnL by hour
    print(f"\n--- PnL by Hour ---")
    hour_stats = rdf.groupby('hour').agg(
        trades=('pnl', 'count'),
        total_pnl=('pnl', 'sum'),
        win_rate=('win', 'mean'),
    ).round(2)
    hour_stats['win_rate'] = (hour_stats['win_rate'] * 100).round(1)
    print(hour_stats.to_string())
    
    # PnL by day
    days = {0:'Mon',1:'Tue',2:'Wed',3:'Thu',4:'Fri',5:'Sat',6:'Sun'}
    print(f"\n--- PnL by Day ---")
    day_stats = rdf.groupby('dow').agg(
        trades=('pnl', 'count'),
        total_pnl=('pnl', 'sum'),
        win_rate=('win', 'mean'),
    ).round(2)
    day_stats.index = day_stats.index.map(lambda x: days.get(x, x))
    day_stats['win_rate'] = (day_stats['win_rate'] * 100).round(1)
    print(day_stats.to_string())
    
    # ATR win vs loss
    print(f"\n--- ATR: Win vs Loss ---")
    wins = rdf[rdf['win']]
    losses = rdf[~rdf['win']]
    print(f"Win trades avg ATR:  {wins['atr'].mean():.2f}")
    print(f"Loss trades avg ATR: {losses['atr'].mean():.2f}")


if __name__ == "__main__":
    for strat in ['structure_break', 'london_breakout']:
        for inst in ['EURUSD']:
            try:
                analyze(strat, inst)
            except Exception as e:
                print(f"Error {strat} {inst}: {e}")
