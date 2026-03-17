"""Break of Structure (BOS) Strategy with EMA 200 trend filter."""
from backtesting import Strategy
from src.indicators.technical import atr_from_cols, ema
import numpy as np


def _swing_highs(high, lookback):
    out = np.full(len(high), np.nan)
    w = max(3, int(lookback) // 5)
    for i in range(w, len(high) - w):
        window = high[i - w:i + w + 1]
        if high[i] == max(window):
            out[i] = high[i]
    return out


def _swing_lows(low, lookback):
    out = np.full(len(low), np.nan)
    w = max(3, int(lookback) // 5)
    for i in range(w, len(low) - w):
        window = low[i - w:i + w + 1]
        if low[i] == min(window):
            out[i] = low[i]
    return out


class StructureBreakStrategy(Strategy):
    lookback = 20
    atr_period = 14
    atr_sl_multiplier = 1.0
    atr_tp_multiplier = 2.5
    ema_trend_period = 200

    def init(self):
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.swing_h = self.I(_swing_highs, self.data.High, self.lookback)
        self.swing_l = self.I(_swing_lows, self.data.Low, self.lookback)
        self.ema200 = self.I(ema, self.data.Close, self.ema_trend_period)
        self._last_sh = None
        self._last_sl = None

    def next(self):
        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return

        if not np.isnan(self.swing_h[-1]):
            self._last_sh = self.swing_h[-1]
        if not np.isnan(self.swing_l[-1]):
            self._last_sl = self.swing_l[-1]

        if self._last_sh is None or self._last_sl is None:
            return

        price = self.data.Close[-1]
        prev = self.data.Close[-2] if len(self.data.Close) > 1 else price
        sl_dist = atr_val * self.atr_sl_multiplier
        tp_dist = atr_val * self.atr_tp_multiplier

        ema200_val = self.ema200[-1]
        if np.isnan(ema200_val):
            return

        # Only buy above EMA 200, only sell below EMA 200
        if price > self._last_sh and prev <= self._last_sh:
            if price > ema200_val:  # Trend filter
                if not self.position.is_long:
                    self.position.close()
                    self.buy(sl=price - sl_dist, tp=price + tp_dist)
                    self._last_sh = price

        elif price < self._last_sl and prev >= self._last_sl:
            if price < ema200_val:  # Trend filter
                if not self.position.is_short:
                    self.position.close()
                    self.sell(sl=price + sl_dist, tp=price - tp_dist)
                    self._last_sl = price
