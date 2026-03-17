"""London Breakout Strategy."""
from backtesting import Strategy
from src.indicators.technical import atr_from_cols
import numpy as np


class LondonBreakoutStrategy(Strategy):
    asian_start = 0   # UTC hour
    asian_end = 7     # UTC hour
    london_start = 7
    london_end = 10
    tp_multiplier = 1.5
    atr_period = 14

    def init(self):
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self._asian_high = None
        self._asian_low = None
        self._traded_today = False
        self._last_date = None

    def next(self):
        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return

        idx = self.data.index[-1]
        # Detect daily data: check if consecutive bars are ~1 day apart
        if len(self.data) >= 2:
            delta = self.data.index[-1] - self.data.index[-2]
            if hasattr(delta, 'total_seconds') and delta.total_seconds() >= 82800:  # >= 23h
                self._daily_breakout(atr_val)
                return

        try:
            hour = idx.hour
            date = idx.date()
        except AttributeError:
            self._daily_breakout(atr_val)
            return

        # Reset on new day
        if self._last_date != date:
            self._asian_high = None
            self._asian_low = None
            self._traded_today = False
            self._last_date = date

        # Collect Asian session range
        if self.asian_start <= hour < self.asian_end:
            h, l = self.data.High[-1], self.data.Low[-1]
            if self._asian_high is None:
                self._asian_high = h
                self._asian_low = l
            else:
                self._asian_high = max(self._asian_high, h)
                self._asian_low = min(self._asian_low, l)

        # London session entry
        elif self.london_start <= hour < self.london_end:
            if self._asian_high is None or self._asian_low is None:
                return
            if self._traded_today:
                return

            asian_range = self._asian_high - self._asian_low
            if asian_range <= 0 or asian_range > atr_val * 2.0:
                return  # Skip if range too wide (choppy)

            price = self.data.Close[-1]
            high = self.data.High[-1]
            low = self.data.Low[-1]
            tp_dist = asian_range * self.tp_multiplier

            # Breakout above Asian high
            if high > self._asian_high and price > self._asian_high:
                sl_dist = price - self._asian_low
                if sl_dist > 0:
                    self.position.close()
                    self.buy(sl=self._asian_low, tp=price + tp_dist)
                    self._traded_today = True
            # Breakout below Asian low
            elif low < self._asian_low and price < self._asian_low:
                sl_dist = self._asian_high - price
                if sl_dist > 0:
                    self.position.close()
                    self.sell(sl=self._asian_high, tp=price - tp_dist)
                    self._traded_today = True

    def _daily_breakout(self, atr_val):
        """Simplified breakout for daily timeframe using 2-bar consolidation range."""
        if len(self.data) < 4:
            return

        # Use previous 2 bars as consolidation range
        recent_high = max(self.data.High[-3], self.data.High[-2])
        recent_low = min(self.data.Low[-3], self.data.Low[-2])
        range_width = recent_high - recent_low

        if range_width <= 0:
            return

        price = self.data.Close[-1]
        tp_dist = range_width * self.tp_multiplier

        if price > recent_high:
            if not self.position.is_long:
                self.position.close()
                self.buy(sl=recent_low, tp=price + tp_dist)
        elif price < recent_low:
            if not self.position.is_short:
                self.position.close()
                self.sell(sl=recent_high, tp=price - tp_dist)
