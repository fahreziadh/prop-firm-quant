"""Momentum detection utilities for session scalping."""
import numpy as np
import pandas as pd


def is_momentum_candle(open_arr, high, low, close, lookback=5, multiplier=2.0):
    """Detect momentum candles where body > multiplier * avg body of last N candles.
    
    Returns: boolean numpy array
    """
    o = np.array(open_arr, dtype=float)
    c = np.array(close, dtype=float)
    bodies = np.abs(c - o)
    n = len(o)
    result = np.zeros(n, dtype=bool)
    for i in range(lookback + 1, n):
        avg_body = np.mean(bodies[i - lookback:i])
        if avg_body > 0 and bodies[i] > multiplier * avg_body:
            result[i] = True
    return result


def atr_expanding(high, low, close, fast=7, slow=20):
    """Check if fast ATR > slow ATR (volatility expansion).
    
    Returns: boolean numpy array
    """
    h = pd.Series(np.array(high, dtype=float))
    l = pd.Series(np.array(low, dtype=float))
    c = pd.Series(np.array(close, dtype=float))
    c_prev = c.shift(1)
    tr = pd.concat([h - l, (h - c_prev).abs(), (l - c_prev).abs()], axis=1).max(axis=1)
    atr_fast = tr.rolling(fast).mean().values
    atr_slow = tr.rolling(slow).mean().values
    result = np.zeros(len(high), dtype=bool)
    valid = ~(np.isnan(atr_fast) | np.isnan(atr_slow))
    result[valid] = atr_fast[valid] > atr_slow[valid]
    return result


def session_open_window(index, session='london'):
    """Return boolean array marking session open windows.
    
    Args:
        index: DatetimeIndex
        session: 'london' (7-8 UTC) or 'ny' (13-14 UTC) or 'both'
    
    Returns: boolean numpy array
    """
    hours = np.array([t.hour for t in index])
    if session == 'london':
        return (hours >= 7) & (hours <= 8)
    elif session == 'ny':
        return (hours >= 13) & (hours <= 14)
    elif session == 'both':
        return ((hours >= 7) & (hours <= 8)) | ((hours >= 13) & (hours <= 14))
    else:
        raise ValueError(f"Unknown session: {session}")
