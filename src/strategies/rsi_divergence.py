"""RSI Divergence + Trend Strategy."""
from backtesting import Strategy
from src.indicators.technical import rsi, ema, atr_from_cols
import numpy as np


def _swing_highs_idx(high, window=5):
    """Return array with swing high values (nan elsewhere)."""
    out = np.full(len(high), np.nan)
    for i in range(window, len(high) - window):
        if high[i] == max(high[i - window:i + window + 1]):
            out[i] = high[i]
    return out


def _swing_lows_idx(low, window=5):
    out = np.full(len(low), np.nan)
    for i in range(window, len(low) - window):
        if low[i] == min(low[i - window:i + window + 1]):
            out[i] = low[i]
    return out


class RSIDivergenceStrategy(Strategy):
    rsi_period = 14
    ema_period = 20
    atr_period = 14
    swing_window = 3
    atr_sl_multiplier = 1.5
    atr_tp_multiplier = 3.0

    def init(self):
        self.rsi_val = self.I(rsi, self.data.Close, self.rsi_period)
        self.ema50 = self.I(ema, self.data.Close, self.ema_period)
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.swing_h = self.I(_swing_highs_idx, self.data.High, self.swing_window)
        self.swing_l = self.I(_swing_lows_idx, self.data.Low, self.swing_window)

    def _recent_swings(self, swing_arr, n=2):
        """Get last n non-nan swing indices and values."""
        results = []
        for i in range(len(self.data) - 1, -1, -1):
            if i >= len(swing_arr):
                continue
            if not np.isnan(swing_arr[i]):
                results.append((i, swing_arr[i]))
                if len(results) >= n:
                    break
        return results  # [(idx, val), ...] most recent first

    def next(self):
        if len(self.data) < self.ema_period + 10:
            return

        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return

        price = self.data.Close[-1]
        trend_up = price > self.ema50[-1]
        trend_down = price < self.ema50[-1]

        # Check bullish divergence: price makes lower low, RSI makes higher low
        if trend_up:
            lows = self._recent_swings(self.swing_l, 2)
            if len(lows) >= 2:
                recent_idx, recent_price = lows[0]
                prev_idx, prev_price = lows[1]
                if recent_price < prev_price:  # price lower low
                    recent_rsi = self.rsi_val[recent_idx] if recent_idx < len(self.rsi_val) else np.nan
                    prev_rsi = self.rsi_val[prev_idx] if prev_idx < len(self.rsi_val) else np.nan
                    if not np.isnan(recent_rsi) and not np.isnan(prev_rsi):
                        if recent_rsi > prev_rsi:  # RSI higher low = bullish divergence
                            if not self.position.is_long:
                                sl = recent_price - atr_val * 0.5
                                sl_dist = price - sl
                                if sl_dist > 0:
                                    tp = price + sl_dist * 2
                                    self.position.close()
                                    self.buy(sl=sl, tp=tp)
                                    return

        # Check bearish divergence: price makes higher high, RSI makes lower high
        if trend_down:
            highs = self._recent_swings(self.swing_h, 2)
            if len(highs) >= 2:
                recent_idx, recent_price = highs[0]
                prev_idx, prev_price = highs[1]
                if recent_price > prev_price:  # price higher high
                    recent_rsi = self.rsi_val[recent_idx] if recent_idx < len(self.rsi_val) else np.nan
                    prev_rsi = self.rsi_val[prev_idx] if prev_idx < len(self.rsi_val) else np.nan
                    if not np.isnan(recent_rsi) and not np.isnan(prev_rsi):
                        if recent_rsi < prev_rsi:  # RSI lower high = bearish divergence
                            if not self.position.is_short:
                                sl = recent_price + atr_val * 0.5
                                sl_dist = sl - price
                                if sl_dist > 0:
                                    tp = price - sl_dist * 2
                                    self.position.close()
                                    self.sell(sl=sl, tp=tp)
                                    return
