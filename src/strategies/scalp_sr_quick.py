"""Scalp S/R Quick — rejection candle at swing high/low levels."""
from backtesting import Strategy
from src.indicators.technical import atr_from_cols
import numpy as np


def _rolling_swing_high(high, period=20):
    """Rolling swing high over last `period` bars."""
    out = np.full(len(high), np.nan)
    for i in range(period, len(high)):
        out[i] = np.max(high[i - period:i])
    return out


def _rolling_swing_low(low, period=20):
    out = np.full(len(low), np.nan)
    for i in range(period, len(low)):
        out[i] = np.min(low[i - period:i])
    return out


class ScalpSRQuickStrategy(Strategy):
    sr_lookback = 20
    atr_period = 14
    wick_body_ratio = 1.5
    sl_atr_mult = 0.5
    tp_rr = 1.5
    risk_pct = 1.0
    atr_min_threshold = 0.3  # skip if ATR < this fraction of avg ATR
    london_start = 7
    london_end = 11
    ny_start = 13
    ny_end = 17

    def init(self):
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.swing_h = self.I(_rolling_swing_high, self.data.High, self.sr_lookback)
        self.swing_l = self.I(_rolling_swing_low, self.data.Low, self.sr_lookback)

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

        o, h, l, c = self.data.Open[-1], self.data.High[-1], self.data.Low[-1], self.data.Close[-1]
        body = abs(c - o)
        if body <= 0:
            return

        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        sh = self.swing_h[-1]
        sl_level = self.swing_l[-1]

        if np.isnan(sh) or np.isnan(sl_level):
            return

        price = c
        proximity_threshold = atr_val * 0.3

        # Bearish rejection at resistance (swing high)
        if abs(h - sh) < proximity_threshold and upper_wick > self.wick_body_ratio * body:
            sl_dist = (sh - price) + atr_val * self.sl_atr_mult
            if sl_dist > 0:
                tp_dist = sl_dist * self.tp_rr
                if not self.position.is_short:
                    self.position.close()
                    self.sell(sl=price + sl_dist, tp=price - tp_dist)

        # Bullish rejection at support (swing low)
        elif abs(l - sl_level) < proximity_threshold and lower_wick > self.wick_body_ratio * body:
            sl_dist = (price - sl_level) + atr_val * self.sl_atr_mult
            if sl_dist > 0:
                tp_dist = sl_dist * self.tp_rr
                if not self.position.is_long:
                    self.position.close()
                    self.buy(sl=price - sl_dist, tp=price + tp_dist)
