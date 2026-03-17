"""Technical indicators - compatible with both pandas and numpy arrays."""
import pandas as pd
import numpy as np


def _to_series(data) -> pd.Series:
    if isinstance(data, pd.Series):
        return data
    return pd.Series(data)


def ema(series, period: int):
    s = _to_series(series)
    return s.ewm(span=period, adjust=False).mean().values


def sma(series, period: int):
    s = _to_series(series)
    return s.rolling(period).mean().values


def rsi(series, period: int = 14):
    s = _to_series(series)
    delta = s.diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / loss
    return (100 - (100 / (1 + rs))).values


def atr_from_cols(high, low, close, period: int = 14):
    """ATR from separate H/L/C arrays - compatible with backtesting.py self.I()."""
    h, l, c = _to_series(high), _to_series(low), _to_series(close)
    c_prev = c.shift(1)
    tr = pd.concat([h - l, (h - c_prev).abs(), (l - c_prev).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean().values


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR from a DataFrame with High/Low/Close columns."""
    h, l, c = df["High"], df["Low"], df["Close"].shift(1)
    tr = pd.concat([h - l, (h - c).abs(), (l - c).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def macd(series, fast: int = 12, slow: int = 26, signal: int = 9):
    s = _to_series(series)
    ema_fast = s.ewm(span=fast, adjust=False).mean()
    ema_slow = s.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series, period: int = 20, std_dev: float = 2.0):
    s = _to_series(series)
    mid = s.rolling(period).mean()
    std = s.rolling(period).std()
    return mid + std_dev * std, mid, mid - std_dev * std


def support_resistance(df: pd.DataFrame, lookback: int = 50, num_levels: int = 5) -> dict:
    """Detect S/R levels using pivot highs/lows."""
    h, l = df["High"].values, df["Low"].values
    n = len(df)
    window = max(5, lookback // 10)
    highs, lows = [], []
    for i in range(window, n - window):
        if h[i] == max(h[i - window:i + window + 1]):
            highs.append(h[i])
        if l[i] == min(l[i - window:i + window + 1]):
            lows.append(l[i])

    all_levels = sorted(highs + lows)
    if not all_levels:
        return {"support": [], "resistance": []}

    price = df["Close"].iloc[-1]
    support = sorted([lv for lv in all_levels if lv < price], reverse=True)[:num_levels]
    resistance = sorted([lv for lv in all_levels if lv >= price])[:num_levels]
    return {"support": support, "resistance": resistance}
