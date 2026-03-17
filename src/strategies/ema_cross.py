"""EMA Crossover Strategy."""
from backtesting import Strategy
from backtesting.lib import crossover
from src.indicators.technical import ema, atr_from_cols


class EMACrossStrategy(Strategy):
    fast_period = 9
    slow_period = 21
    atr_period = 14
    atr_sl_multiplier = 1.5
    atr_tp_multiplier = 3.0

    def init(self):
        self.ema_fast = self.I(ema, self.data.Close, self.fast_period)
        self.ema_slow = self.I(ema, self.data.Close, self.slow_period)
        self.atr = self.I(atr_from_cols, self.data.High, self.data.Low, self.data.Close, self.atr_period)

    def next(self):
        atr_val = self.atr[-1]
        if np.isnan(atr_val) or atr_val <= 0:
            return

        price = self.data.Close[-1]
        sl_dist = atr_val * self.atr_sl_multiplier
        tp_dist = atr_val * self.atr_tp_multiplier

        if crossover(self.ema_fast, self.ema_slow):
            self.buy(sl=price - sl_dist, tp=price + tp_dist)
        elif crossover(self.ema_slow, self.ema_fast):
            self.sell(sl=price + sl_dist, tp=price - tp_dist)


import numpy as np
