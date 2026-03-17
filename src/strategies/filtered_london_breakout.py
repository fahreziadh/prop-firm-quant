"""London Breakout Strategy with Conviction Scoring filter."""
from src.strategies.london_breakout import LondonBreakoutStrategy
from src.strategies.conviction_scorer import ConvictionScorer
import numpy as np


class FilteredLondonBreakoutStrategy(LondonBreakoutStrategy):
    min_score = 50

    def init(self):
        super().init()
        self._scorer = ConvictionScorer(
            self.data.High, self.data.Low, self.data.Close,
            index=self.data.index
        )

    def next(self):
        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return

        idx = self.data.index[-1]
        if len(self.data) >= 2:
            delta = self.data.index[-1] - self.data.index[-2]
            if hasattr(delta, 'total_seconds') and delta.total_seconds() >= 82800:
                self._filtered_daily_breakout(atr_val)
                return

        try:
            hour = idx.hour
            date = idx.date()
            dow = idx.weekday()
        except AttributeError:
            self._filtered_daily_breakout(atr_val)
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

    def _filtered_daily_breakout(self, atr_val):
        # Fallback to parent for daily data (no filtering since no intraday info)
        super()._daily_breakout(atr_val)
