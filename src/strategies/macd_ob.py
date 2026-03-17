"""MACD + Order Block Strategy."""
from backtesting import Strategy
from src.indicators.technical import atr_from_cols
import numpy as np


def _macd_hist(close, fast=12, slow=26, signal=9):
    """MACD histogram as numpy array."""
    from src.indicators.technical import _to_series
    s = _to_series(close)
    ema_fast = s.ewm(span=fast, adjust=False).mean()
    ema_slow = s.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return (macd_line - signal_line).values


class MACDOrderBlockStrategy(Strategy):
    atr_period = 14
    ob_lookback = 30
    atr_sl_multiplier = 1.0
    atr_tp_multiplier = 2.0
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9

    def init(self):
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.hist = self.I(_macd_hist, self.data.Close, self.macd_fast, self.macd_slow, self.macd_signal)

    def _find_order_blocks(self):
        """Find bullish and bearish order blocks."""
        n = len(self.data)
        lookback = min(self.ob_lookback, n - 2)
        bullish_ob = None  # Last bearish candle before bullish move
        bearish_ob = None  # Last bullish candle before bearish move

        for i in range(n - 2, max(n - lookback - 2, 1), -1):
            o, c = self.data.Open[i], self.data.Close[i]
            o_next, c_next = self.data.Open[i + 1], self.data.Close[i + 1]

            if bullish_ob is None:
                # Bearish candle followed by bullish candle (bullish OB)
                if c < o and c_next > o_next and (c_next - o_next) > abs(c - o):
                    bullish_ob = {
                        'high': max(o, c),
                        'low': min(o, c),
                        'idx': i,
                    }

            if bearish_ob is None:
                # Bullish candle followed by bearish candle (bearish OB)
                if c > o and c_next < o_next and (o_next - c_next) > abs(c - o):
                    bearish_ob = {
                        'high': max(o, c),
                        'low': min(o, c),
                        'idx': i,
                    }

            if bullish_ob and bearish_ob:
                break

        return bullish_ob, bearish_ob

    def next(self):
        if len(self.data) < self.macd_slow + self.macd_signal + 5:
            return

        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return

        hist_curr = self.hist[-1]
        hist_prev = self.hist[-2]
        if np.isnan(hist_curr) or np.isnan(hist_prev):
            return

        price = self.data.Close[-1]
        bullish_ob, bearish_ob = self._find_order_blocks()

        # Bullish: price retraces to bullish OB + MACD histogram flips positive
        if bullish_ob and hist_prev <= 0 and hist_curr > 0:
            ob = bullish_ob
            if ob['low'] * 0.995 <= price <= ob['high'] * 1.01:
                sl = ob['low'] - atr_val * 0.3
                sl_dist = price - sl
                if sl_dist > 0:
                    tp = price + sl_dist * 2
                    if not self.position.is_long:
                        self.position.close()
                        self.buy(sl=sl, tp=tp)
                    return

        # Bearish: price retraces to bearish OB + MACD histogram flips negative
        if bearish_ob and hist_prev >= 0 and hist_curr < 0:
            ob = bearish_ob
            if ob['low'] * 0.99 <= price <= ob['high'] * 1.005:
                sl = ob['high'] + atr_val * 0.3
                sl_dist = sl - price
                if sl_dist > 0:
                    tp = price - sl_dist * 2
                    if not self.position.is_short:
                        self.position.close()
                        self.sell(sl=sl, tp=tp)
                    return
