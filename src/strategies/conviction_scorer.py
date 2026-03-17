"""Conviction Scoring System — scores potential trades 0-100."""
import numpy as np
import pandas as pd
from src.indicators.technical import ema, rsi, macd, atr_from_cols


class ConvictionScorer:
    """Score a potential trade from 0-100 across 5 factors (each 0-20)."""

    def __init__(self, high, low, close, index=None,
                 ema_fast_period=50, ema_slow_period=200,
                 rsi_period=14, atr_period=14,
                 sr_levels=None):
        self.high = np.asarray(high, dtype=float)
        self.low = np.asarray(low, dtype=float)
        self.close = np.asarray(close, dtype=float)
        self.index = index

        # Pre-compute indicators
        self.ema50 = ema(close, ema_fast_period)
        self.ema200 = ema(close, ema_slow_period)
        self.rsi_vals = rsi(close, rsi_period)
        macd_line, signal_line, histogram = macd(close)
        self.macd_hist = np.asarray(histogram)
        self.atr_vals = atr_from_cols(high, low, close, atr_period)
        self.sr_levels = sr_levels or []

    def score(self, bar_index: int, direction: str) -> dict:
        """Score a trade at bar_index. direction='long' or 'short'.
        bar_index uses negative indexing or is clamped to array bounds.
        Returns dict with total score and breakdown."""
        is_long = direction == 'long'
        # Clamp to valid range
        n = len(self.close)
        if bar_index < 0:
            bar_index = n + bar_index
        bar_index = min(bar_index, n - 1)

        t = self._trend_alignment(bar_index, is_long)
        m = self._momentum(bar_index, is_long)
        k = self._key_level_proximity(bar_index, is_long)
        v = self._volatility_quality(bar_index)
        s = self._session_timing(bar_index)

        total = t + m + k + v + s
        return {
            'total': total,
            'trend': t,
            'momentum': m,
            'key_level': k,
            'volatility': v,
            'session': s,
        }

    def _trend_alignment(self, i: int, is_long: bool) -> int:
        e50 = self.ema50[i]
        e200 = self.ema200[i]
        price = self.close[i]
        if np.isnan(e50) or np.isnan(e200):
            return 10

        if is_long:
            above50 = price > e50
            above200 = price > e200
        else:
            above50 = price < e50
            above200 = price < e200

        if above50 and above200:
            return 20
        elif above50 or above200:
            return 10
        return 0

    def _momentum(self, i: int, is_long: bool) -> int:
        score = 0
        r = self.rsi_vals[i]
        if np.isnan(r):
            return 10

        if is_long:
            if 40 <= r <= 60:
                score = 15 + int((60 - abs(r - 50)) / 10 * 5)  # 15-20
            elif r > 60:
                score = 10  # overbought but long - moderate
            elif r < 30:
                score = 15  # oversold reversal long
            else:
                score = 5
        else:
            if 40 <= r <= 60:
                score = 15 + int((60 - abs(r - 50)) / 10 * 5)
            elif r < 40:
                score = 10
            elif r > 70:
                score = 15  # overbought reversal short
            else:
                score = 5

        score = min(score, 15)

        # MACD histogram bonus
        hist = self.macd_hist[i]
        if not np.isnan(hist):
            if (is_long and hist > 0) or (not is_long and hist < 0):
                score += 5

        return min(score, 20)

    def _key_level_proximity(self, i: int, is_long: bool) -> int:
        if not self.sr_levels:
            return 5

        price = self.close[i]
        atr_val = self.atr_vals[i]
        if np.isnan(atr_val) or atr_val <= 0:
            return 5

        min_dist = float('inf')
        for level in self.sr_levels:
            dist = abs(price - level)
            min_dist = min(min_dist, dist)

        ratio = min_dist / atr_val
        if ratio <= 0.5:
            return 20
        elif ratio <= 1.0:
            return 10
        return 5

    def _volatility_quality(self, i: int) -> int:
        atr_val = self.atr_vals[i]
        if np.isnan(atr_val):
            return 10

        # Get ATR percentile over last 100 bars
        start = max(0, i - 99)
        window = self.atr_vals[start:i + 1]
        valid = window[~np.isnan(window)]
        if len(valid) < 10:
            return 10

        pct = np.sum(valid < atr_val) / len(valid) * 100
        if 25 <= pct <= 75:
            return 20
        elif 15 <= pct <= 85:
            return 15
        elif 10 <= pct <= 90:
            return 10
        return 5

    def _session_timing(self, i: int) -> int:
        if self.index is None:
            return 10
        try:
            hour = self.index[i].hour
        except (AttributeError, IndexError):
            return 10

        # London open: 7-9 UTC, NY open: 13-15 UTC
        if hour in (7, 8, 13, 14):
            return 20
        # London active: 9-12, NY active: 15-17
        elif 9 <= hour <= 12 or 15 <= hour <= 17:
            return 15
        # Asian: 0-6 UTC
        elif 0 <= hour <= 6:
            return 5
        # Off hours
        return 0
