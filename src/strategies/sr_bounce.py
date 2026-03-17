"""Support/Resistance Bounce Strategy with rejection candle filter."""
from backtesting import Strategy
from src.indicators.technical import atr_from_cols, rsi
import numpy as np


class SRBounceStrategy(Strategy):
    lookback = 50
    zone_threshold = 0.002
    atr_period = 14
    atr_sl_multiplier = 1.0
    atr_tp_multiplier = 2.0
    wick_body_ratio = 1.5

    def init(self):
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.rsi = self.I(rsi, self.data.Close, 14)
        self._levels = None
        self._levels_bar = -1

    def _compute_levels(self):
        h, l = np.array(self.data.High), np.array(self.data.Low)
        levels = []
        w = max(5, self.lookback // 10)
        n = len(h)
        for i in range(w, n - w):
            if h[i] == max(h[i - w:i + w + 1]):
                levels.append(h[i])
            if l[i] == min(l[i - w:i + w + 1]):
                levels.append(l[i])
        return sorted(set(levels))

    def _is_rejection_candle(self):
        """Check if current candle has rejection wick > 1.5x body size."""
        o = self.data.Open[-1]
        c = self.data.Close[-1]
        h = self.data.High[-1]
        l = self.data.Low[-1]
        body = abs(c - o)
        if body == 0:
            body = 0.0001  # avoid division by zero
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        # For bullish rejection: lower wick should be large
        # For bearish rejection: upper wick should be large
        return upper_wick, lower_wick, body

    def next(self):
        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return

        bar = len(self.data)
        if self._levels is None or bar - self._levels_bar > 50:
            self._levels = self._compute_levels()
            self._levels_bar = bar

        price = self.data.Close[-1]
        threshold = price * self.zone_threshold
        sl_dist = atr_val * self.atr_sl_multiplier
        tp_dist = atr_val * self.atr_tp_multiplier

        upper_wick, lower_wick, body = self._is_rejection_candle()

        for level in self._levels:
            if abs(price - level) < threshold:
                rsi_val = self.rsi[-1]
                # Bullish bounce: lower wick > 1.5x body
                if price >= level and rsi_val < 35:
                    if lower_wick > body * self.wick_body_ratio:
                        if not self.position.is_long:
                            self.position.close()
                            self.buy(sl=price - sl_dist, tp=price + tp_dist)
                        return
                # Bearish bounce: upper wick > 1.5x body
                elif price <= level and rsi_val > 65:
                    if upper_wick > body * self.wick_body_ratio:
                        if not self.position.is_short:
                            self.position.close()
                            self.sell(sl=price + sl_dist, tp=price - tp_dist)
                        return
