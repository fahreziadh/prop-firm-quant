"""High Conviction Strategy — combines Structure Break + London Breakout with conviction scoring."""
from backtesting import Strategy
from src.indicators.technical import atr_from_cols, ema
from src.strategies.conviction_scorer import ConvictionScorer
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


class HighConvictionStrategy(Strategy):
    lookback = 20
    atr_period = 14
    atr_sl_multiplier = 1.0
    atr_tp_multiplier = 2.5
    ema_trend_period = 200
    min_score = 60
    full_size_score = 80
    asian_start = 0
    asian_end = 7
    london_start = 7
    london_end = 10
    tp_multiplier = 1.5
    asian_range_min_pct = 0.30
    asian_range_max_pct = 0.80

    def init(self):
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.swing_h = self.I(_swing_highs, self.data.High, self.lookback)
        self.swing_l = self.I(_swing_lows, self.data.Low, self.lookback)
        self.ema200 = self.I(ema, self.data.Close, self.ema_trend_period)
        self._last_sh = None
        self._last_sl = None
        self._asian_high = None
        self._asian_low = None
        self._traded_today = False
        self._last_date = None
        # Build S/R levels and scorer in init where full data is available
        sr = []
        sh = np.asarray(self.swing_h)
        sl_arr = np.asarray(self.swing_l)
        for v in sh[~np.isnan(sh)]:
            sr.append(float(v))
        for v in sl_arr[~np.isnan(sl_arr)]:
            sr.append(float(v))
        self._scorer = ConvictionScorer(
            self.data.High, self.data.Low, self.data.Close,
            index=self.data.index, sr_levels=sr
        )

    def next(self):
        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return

        # Try structure break signal
        self._check_structure_break(atr_val)
        # Try london breakout signal
        self._check_london_breakout(atr_val)

    def _check_structure_break(self, atr_val):
        if not np.isnan(self.swing_h[-1]):
            self._last_sh = self.swing_h[-1]
        if not np.isnan(self.swing_l[-1]):
            self._last_sl = self.swing_l[-1]

        if self._last_sh is None or self._last_sl is None:
            return

        price = self.data.Close[-1]
        prev = self.data.Close[-2] if len(self.data.Close) > 1 else price
        ema200_val = self.ema200[-1]
        if np.isnan(ema200_val):
            return

        sl_dist = atr_val * self.atr_sl_multiplier
        tp_dist = atr_val * self.atr_tp_multiplier
        bar_i = len(self.data.Close) - 1

        if price > self._last_sh and prev <= self._last_sh and price > ema200_val:
            result = self._scorer.score(bar_i, 'long')
            if result['total'] >= self.min_score:
                if not self.position.is_long:
                    self.position.close()
                    self.buy(sl=price - sl_dist, tp=price + tp_dist)
                    self._last_sh = price

        elif price < self._last_sl and prev >= self._last_sl and price < ema200_val:
            result = self._scorer.score(bar_i, 'short')
            if result['total'] >= self.min_score:
                if not self.position.is_short:
                    self.position.close()
                    self.sell(sl=price + sl_dist, tp=price - tp_dist)
                    self._last_sl = price

    def _check_london_breakout(self, atr_val):
        idx = self.data.index[-1]
        try:
            hour = idx.hour
            date = idx.date()
            dow = idx.weekday()
        except AttributeError:
            return

        if dow == 0 or dow == 4:
            return

        if self._last_date != date:
            self._asian_high = None
            self._asian_low = None
            self._traded_today = False
            self._last_date = date

        if self.asian_start <= hour < self.asian_end:
            h, l = self.data.High[-1], self.data.Low[-1]
            if self._asian_high is None:
                self._asian_high = h
                self._asian_low = l
            else:
                self._asian_high = max(self._asian_high, h)
                self._asian_low = min(self._asian_low, l)

        elif self.london_start <= hour < self.london_end:
            if self._asian_high is None or self._asian_low is None:
                return
            if self._traded_today:
                return

            asian_range = self._asian_high - self._asian_low
            if asian_range <= 0:
                return
            range_ratio = asian_range / atr_val
            if range_ratio < self.asian_range_min_pct or range_ratio > self.asian_range_max_pct:
                return

            price = self.data.Close[-1]
            tp_dist = asian_range * self.tp_multiplier
            bar_i = len(self.data.Close) - 1

            if price > self._asian_high:
                result = self._scorer.score(bar_i, 'long')
                if result['total'] >= self.min_score:
                    self.position.close()
                    self.buy(sl=self._asian_low, tp=price + tp_dist)
                    self._traded_today = True

            elif price < self._asian_low:
                result = self._scorer.score(bar_i, 'short')
                if result['total'] >= self.min_score:
                    self.position.close()
                    self.sell(sl=self._asian_high, tp=price - tp_dist)
                    self._traded_today = True
