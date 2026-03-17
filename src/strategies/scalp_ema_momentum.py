"""Scalp EMA Momentum — M15 EMA crossover with RSI confirmation and session filter."""
from backtesting import Strategy
from src.indicators.technical import atr_from_cols, ema, rsi
import numpy as np


class ScalpEMAMomentumStrategy(Strategy):
    ema_fast = 9
    ema_slow = 21
    ema_trend = 200
    rsi_period = 7
    atr_period = 14
    atr_sl_mult = 1.0
    atr_tp_mult = 1.5
    risk_pct = 1.0
    # Session hours (UTC)
    london_start = 7
    london_end = 11
    ny_start = 13
    ny_end = 17

    def init(self):
        self.ema9 = self.I(ema, self.data.Close, self.ema_fast)
        self.ema21 = self.I(ema, self.data.Close, self.ema_slow)
        self.ema200 = self.I(ema, self.data.Close, self.ema_trend)
        self.rsi7 = self.I(rsi, self.data.Close, self.rsi_period)
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)

    def _in_session(self):
        try:
            h = self.data.index[-1].hour
        except AttributeError:
            return False
        return (self.london_start <= h < self.london_end) or (self.ny_start <= h < self.ny_end)

    def next(self):
        if len(self.data.Close) < 2:
            return
        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return
        if np.isnan(self.ema200[-1]):
            return
        if not self._in_session():
            return

        price = self.data.Close[-1]
        sl_dist = atr_val * self.atr_sl_mult
        tp_dist = atr_val * self.atr_tp_mult

        # EMA cross detection
        cross_up = self.ema9[-1] > self.ema21[-1] and self.ema9[-2] <= self.ema21[-2]
        cross_down = self.ema9[-1] < self.ema21[-1] and self.ema9[-2] >= self.ema21[-2]

        # Long
        if cross_up and self.rsi7[-1] > 50 and price > self.ema200[-1]:
            if not self.position.is_long:
                self.position.close()
                self.buy(sl=price - sl_dist, tp=price + tp_dist)

        # Short
        elif cross_down and self.rsi7[-1] < 50 and price < self.ema200[-1]:
            if not self.position.is_short:
                self.position.close()
                self.sell(sl=price + sl_dist, tp=price - tp_dist)
