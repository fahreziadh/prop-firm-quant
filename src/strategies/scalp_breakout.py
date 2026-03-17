"""Scalp Breakout — H1 level breakout on M15 with momentum filter."""
from backtesting import Strategy
from src.indicators.technical import atr_from_cols
import numpy as np


def _h1_high(high, close):
    """Previous H1 candle high — approximated as max of last 4 M15 bars (excluding current)."""
    out = np.full(len(high), np.nan)
    for i in range(5, len(high)):
        out[i] = np.max(high[i - 4:i])
    return out


def _h1_low(low, close):
    out = np.full(len(low), np.nan)
    for i in range(5, len(low)):
        out[i] = np.min(low[i - 4:i])
    return out


def _avg_body(open_arr, close_arr, period=10):
    """Rolling average candle body size."""
    out = np.full(len(open_arr), np.nan)
    bodies = np.abs(np.array(close_arr, dtype=float) - np.array(open_arr, dtype=float))
    for i in range(period, len(bodies)):
        out[i] = np.mean(bodies[i - period:i])
    return out


class ScalpBreakoutStrategy(Strategy):
    atr_period = 14
    body_avg_period = 10
    tp_rr = 2.0
    risk_pct = 1.0
    london_start = 7
    london_end = 11
    ny_start = 13
    ny_end = 17

    def init(self):
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.h1_high = self.I(_h1_high, self.data.High, self.data.Close)
        self.h1_low = self.I(_h1_low, self.data.Low, self.data.Close)
        self.avg_body = self.I(_avg_body, self.data.Open, self.data.Close, self.body_avg_period)

    def _in_session(self):
        try:
            h = self.data.index[-1].hour
        except AttributeError:
            return False
        return (self.london_start <= h < self.london_end) or (self.ny_start <= h < self.ny_end)

    def next(self):
        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return
        if not self._in_session():
            return

        # ATR momentum filter: current ATR > average (use atr from last few bars)
        if len(self.data.Close) < self.atr_period + 5:
            return

        o, h, l, c = self.data.Open[-1], self.data.High[-1], self.data.Low[-1], self.data.Close[-1]
        body = abs(c - o)
        avg_b = self.avg_body[-1]
        if np.isnan(avg_b) or avg_b <= 0:
            return

        h1_h = self.h1_high[-1]
        h1_l = self.h1_low[-1]
        if np.isnan(h1_h) or np.isnan(h1_l):
            return

        # Momentum filter: body bigger than average
        if body <= avg_b:
            return

        # Bullish breakout
        if c > h1_h and c > o:  # close above H1 high, bullish candle
            sl_dist = c - l  # SL at opposite side of breakout candle
            if sl_dist > 0:
                tp_dist = sl_dist * self.tp_rr
                if not self.position.is_long:
                    self.position.close()
                    self.buy(sl=c - sl_dist, tp=c + tp_dist)

        # Bearish breakout
        elif c < h1_l and c < o:  # close below H1 low, bearish candle
            sl_dist = h - c  # SL at top of breakout candle
            if sl_dist > 0:
                tp_dist = sl_dist * self.tp_rr
                if not self.position.is_short:
                    self.position.close()
                    self.sell(sl=c + sl_dist, tp=c - tp_dist)
