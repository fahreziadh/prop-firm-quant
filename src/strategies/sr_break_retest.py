"""Support/Resistance Break and Retest Strategy.

Logic:
1. Identify S/R levels via swing highs/lows (50-bar window), validated by 2+ touches
2. Detect breakout: close beyond level with strong body (> avg of last 10)
3. Wait for retest within 10 bars: price returns to level (within 0.3%)
4. Entry on rejection candle at retest (wick > 1.5x body, close in breakout direction)
5. SL: behind broken level + 1x ATR(14)
6. TP: 2x SL distance (R:R 1:2)
7. Filters: EMA200 trend, ATR percentile 25-75, news blackout
"""
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


class SRBreakRetestStrategy(Strategy):
    lookback = 50
    atr_period = 14
    ema_trend_period = 200
    zone_threshold = 0.002   # 0.2% for level validation (touch detection)
    retest_threshold = 0.003  # 0.3% for retest proximity
    retest_window = 10       # bars to wait for retest after breakout
    wick_body_ratio = 1.5    # rejection candle filter
    min_touches = 2          # minimum touches to validate a level
    rr_ratio = 2.0           # risk:reward ratio

    news_filter_enabled = False

    def init(self):
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.swing_h = self.I(_swing_highs, self.data.High, self.lookback)
        self.swing_l = self.I(_swing_lows, self.data.Low, self.lookback)
        self.ema200 = self.I(ema, self.data.Close, self.ema_trend_period)

        # State tracking
        self._levels = []          # validated S/R levels
        self._levels_bar = -1
        self._breakouts = []       # list of (level, direction, bar_index)

    def _compute_validated_levels(self):
        """Find S/R levels with at least min_touches touches."""
        n = len(self.data)
        # Collect all swing points
        raw_levels = []
        for i in range(n):
            if not np.isnan(self.swing_h[i]):
                raw_levels.append(self.swing_h[i])
            if not np.isnan(self.swing_l[i]):
                raw_levels.append(self.swing_l[i])

        if not raw_levels:
            return []

        # Cluster nearby levels and count touches
        raw_levels.sort()
        clusters = []
        used = [False] * len(raw_levels)

        for i, lv in enumerate(raw_levels):
            if used[i]:
                continue
            cluster = [lv]
            used[i] = True
            for j in range(i + 1, len(raw_levels)):
                if used[j]:
                    continue
                if abs(raw_levels[j] - lv) / lv < self.zone_threshold:
                    cluster.append(raw_levels[j])
                    used[j] = True
                elif raw_levels[j] - lv > lv * self.zone_threshold:
                    break
            if len(cluster) >= self.min_touches:
                clusters.append(np.mean(cluster))

        # Also count how many bars touched each level (high/low within threshold)
        validated = []
        highs = np.array(self.data.High)
        lows = np.array(self.data.Low)
        for level in clusters:
            thresh = level * self.zone_threshold
            touches = np.sum((highs >= level - thresh) & (lows <= level + thresh))
            if touches >= self.min_touches:
                validated.append(level)

        return validated

    def _avg_body_size(self, n=10):
        """Average candle body size of last n bars."""
        bodies = []
        for i in range(1, min(n + 1, len(self.data))):
            bodies.append(abs(self.data.Close[-i] - self.data.Open[-i]))
        return np.mean(bodies) if bodies else 0

    def _is_rejection_candle(self, direction):
        """Check if current candle is a rejection candle in the given direction.
        direction: 'long' or 'short'
        """
        o = self.data.Open[-1]
        c = self.data.Close[-1]
        h = self.data.High[-1]
        l = self.data.Low[-1]
        body = abs(c - o)
        if body < 1e-10:
            return False

        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l

        if direction == 'long':
            # Bullish rejection: lower wick > 1.5x body, close above open
            return lower_wick > body * self.wick_body_ratio and c > o
        else:
            # Bearish rejection: upper wick > 1.5x body, close below open
            return upper_wick > body * self.wick_body_ratio and c < o

    def next(self):
        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return

        ema200_val = self.ema200[-1]
        if np.isnan(ema200_val):
            return

        # News filter
        if self.news_filter_enabled:
            try:
                if self.data.news_blackout[-1]:
                    return
            except AttributeError:
                pass

        bar = len(self.data)
        price = self.data.Close[-1]

        # Recompute levels every 50 bars
        if self._levels_bar < 0 or bar - self._levels_bar > 50:
            self._levels = self._compute_validated_levels()
            self._levels_bar = bar

        # ATR percentile filter (25-75 of last 100 bars)
        atr_lookback = min(100, len(self.data))
        if atr_lookback >= 20:
            recent_atrs = [self.atr[-i] for i in range(1, atr_lookback + 1) if not np.isnan(self.atr[-i])]
            if recent_atrs:
                p25 = np.percentile(recent_atrs, 25)
                p75 = np.percentile(recent_atrs, 75)
                if atr_val < p25 or atr_val > p75:
                    # Still check for retests on existing breakouts, but don't detect new breakouts
                    pass  # We allow retest checks but skip new breakout detection below
                    # Actually, let's filter both for simplicity
                    self._check_retests(price, atr_val, ema200_val, bar)
                    return

        # Check existing breakouts for retest opportunities
        self._check_retests(price, atr_val, ema200_val, bar)

        # Detect new breakouts
        if len(self.data) < 2:
            return

        prev_close = self.data.Close[-2]
        avg_body = self._avg_body_size(10)
        current_body = abs(price - self.data.Open[-1])

        # Only consider breakouts with strong momentum
        if current_body <= avg_body:
            return

        for level in self._levels:
            thresh = level * self.zone_threshold

            # Bullish breakout: close above resistance
            if price > level + thresh and prev_close <= level + thresh:
                if price > ema200_val:  # Trend filter: longs only above EMA200
                    self._breakouts.append((level, 'long', bar))

            # Bearish breakout: close below support
            elif price < level - thresh and prev_close >= level - thresh:
                if price < ema200_val:  # Trend filter: shorts only below EMA200
                    self._breakouts.append((level, 'short', bar))

    def _check_retests(self, price, atr_val, ema200_val, bar):
        """Check if price is retesting any broken level."""
        remaining = []
        for level, direction, breakout_bar in self._breakouts:
            bars_since = bar - breakout_bar
            if bars_since > self.retest_window:
                continue  # Expired

            remaining.append((level, direction, breakout_bar))

            # Check if price is near the broken level (retest)
            retest_thresh = level * self.retest_threshold
            if abs(price - level) > retest_thresh:
                continue

            # Check rejection candle
            if not self._is_rejection_candle(direction):
                continue

            # Verify trend filter still valid
            if direction == 'long' and price <= ema200_val:
                continue
            if direction == 'short' and price >= ema200_val:
                continue

            # Verify close is in breakout direction relative to level
            if direction == 'long' and price <= level:
                continue
            if direction == 'short' and price >= level:
                continue

            # Entry!
            sl_dist = abs(price - level) + atr_val  # Behind level + 1 ATR
            tp_dist = sl_dist * self.rr_ratio

            if direction == 'long':
                if not self.position.is_long:
                    self.position.close()
                    sl = level - atr_val
                    sl_dist = price - sl
                    tp = price + sl_dist * self.rr_ratio
                    self.buy(sl=sl, tp=tp)
            else:
                if not self.position.is_short:
                    self.position.close()
                    sl = level + atr_val
                    sl_dist = sl - price
                    tp = price - sl_dist * self.rr_ratio
                    self.sell(sl=sl, tp=tp)

            # Remove this breakout after entry
            remaining = [b for b in remaining if b != (level, direction, breakout_bar)]
            break

        self._breakouts = remaining
