"""Session Open Momentum Scalping — trade London/NY open with momentum breakouts of H1 levels."""
from backtesting import Strategy
from src.indicators.technical import atr_from_cols, ema
from src.indicators.momentum import is_momentum_candle, atr_expanding
import numpy as np


def _h1_swing_high(high, period=96):
    """Rolling max of last 'period' M15 bars (24h = 96 bars)."""
    out = np.full(len(high), np.nan)
    h = np.array(high, dtype=float)
    for i in range(period, len(h)):
        out[i] = np.max(h[i - period:i])
    return out


def _h1_swing_low(low, period=96):
    """Rolling min of last 'period' M15 bars."""
    out = np.full(len(low), np.nan)
    l = np.array(low, dtype=float)
    for i in range(period, len(l)):
        out[i] = np.min(l[i - period:i])
    return out


def _session_high(high, index):
    """Previous session high (last 8 bars = 2h of M15)."""
    out = np.full(len(high), np.nan)
    h = np.array(high, dtype=float)
    for i in range(8, len(h)):
        out[i] = np.max(h[i - 8:i])
    return out


def _session_low(low, index):
    """Previous session low (last 8 bars = 2h of M15)."""
    out = np.full(len(low), np.nan)
    l = np.array(low, dtype=float)
    for i in range(8, len(l)):
        out[i] = np.min(l[i - 8:i])
    return out


class ScalpSessionMomentumStrategy(Strategy):
    # Parameters
    tp_rr = 1.5           # TP as multiple of SL distance
    risk_pct = 1.0        # % equity risk per trade
    ema_period = 50
    atr_period = 14
    momentum_lookback = 5
    momentum_multiplier = 2.0
    atr_fast = 7
    atr_slow = 20
    h1_lookback = 96      # 24h of M15 bars
    max_sl_atr_mult = 1.5 # Max SL width as ATR multiple
    atr_buffer = 0.3      # ATR buffer added to SL
    max_trades_per_session = 2
    max_trades_per_day = 3
    skip_monday_london = True
    news_filter_enabled = False

    def init(self):
        self.atr14 = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.ema50 = self.I(ema, self.data.Close, self.ema_period)
        self.h1_high = self.I(_h1_swing_high, self.data.High, self.h1_lookback)
        self.h1_low = self.I(_h1_swing_low, self.data.Low, self.h1_lookback)
        self.sess_high = self.I(_session_high, self.data.High, self.data.Close)  # dummy 2nd arg
        self.sess_low = self.I(_session_low, self.data.Low, self.data.Close)
        self.is_momentum = self.I(is_momentum_candle, self.data.Open, self.data.High,
                                   self.data.Low, self.data.Close,
                                   self.momentum_lookback, self.momentum_multiplier)
        self.atr_exp = self.I(atr_expanding, self.data.High, self.data.Low, self.data.Close,
                              self.atr_fast, self.atr_slow)

        # Trade counting
        self._session_trades = 0
        self._day_trades = 0
        self._last_session = None
        self._last_day = None

    def _get_session(self, hour):
        """Return session name or None."""
        if 7 <= hour <= 8:
            return 'london'
        elif 13 <= hour <= 14:
            return 'ny'
        return None

    def _in_session(self):
        try:
            idx = self.data.index[-1]
            h = idx.hour
            return self._get_session(h) is not None
        except AttributeError:
            return False

    def next(self):
        try:
            idx = self.data.index[-1]
            hour = idx.hour
            dow = idx.weekday()  # 0=Monday
            day = idx.date()
        except AttributeError:
            return

        # Session check
        session = self._get_session(hour)
        if session is None:
            return

        # Skip Monday London
        if self.skip_monday_london and dow == 0 and session == 'london':
            return

        # News blackout
        if self.news_filter_enabled and hasattr(self.data, 'news_blackout'):
            try:
                if self.data.news_blackout[-1]:
                    return
            except (IndexError, AttributeError):
                pass

        # Trade counting - reset per session/day
        session_key = f"{day}_{session}"
        if session_key != self._last_session:
            self._session_trades = 0
            self._last_session = session_key
        if day != self._last_day:
            self._day_trades = 0
            self._last_day = day

        # Check limits
        if self._session_trades >= self.max_trades_per_session:
            return
        if self._day_trades >= self.max_trades_per_day:
            return

        # Skip if already in position
        if self.position:
            return

        # Check indicators
        atr_val = self.atr14[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return

        ema_val = self.ema50[-1]
        if np.isnan(ema_val):
            return

        h1_h = self.h1_high[-1]
        h1_l = self.h1_low[-1]
        if np.isnan(h1_h) or np.isnan(h1_l):
            return

        # Both momentum conditions must be true
        if not self.is_momentum[-1]:
            return
        if not self.atr_exp[-1]:
            return

        o = self.data.Open[-1]
        h = self.data.High[-1]
        l = self.data.Low[-1]
        c = self.data.Close[-1]
        body = abs(c - o)

        # Use both H1 swing levels and session levels
        # Pick the nearest relevant level
        levels_above = [lv for lv in [h1_h, self.sess_high[-1]] if not np.isnan(lv)]
        levels_below = [lv for lv in [h1_l, self.sess_low[-1]] if not np.isnan(lv)]

        atr_buffer = self.atr_buffer * atr_val

        # BULLISH: momentum candle breaks above a resistance level, aligned with EMA
        if c > o and c > ema_val:  # bullish candle above EMA
            broken_level = None
            for lv in levels_above:
                if o <= lv and c > lv:  # candle opened below, closed above
                    broken_level = lv
                    break
            if broken_level is not None:
                sl_dist = (c - l) + atr_buffer
                if sl_dist > self.max_sl_atr_mult * atr_val:
                    return  # SL too wide
                if sl_dist <= 0:
                    return
                tp_dist = sl_dist * self.tp_rr
                self.buy(sl=c - sl_dist, tp=c + tp_dist)
                self._session_trades += 1
                self._day_trades += 1
                return

        # BEARISH: momentum candle breaks below a support level, aligned with EMA
        if c < o and c < ema_val:  # bearish candle below EMA
            broken_level = None
            for lv in levels_below:
                if o >= lv and c < lv:  # candle opened above, closed below
                    broken_level = lv
                    break
            if broken_level is not None:
                sl_dist = (h - c) + atr_buffer
                if sl_dist > self.max_sl_atr_mult * atr_val:
                    return  # SL too wide
                if sl_dist <= 0:
                    return
                tp_dist = sl_dist * self.tp_rr
                self.sell(sl=c + sl_dist, tp=c - tp_dist)
                self._session_trades += 1
                self._day_trades += 1
