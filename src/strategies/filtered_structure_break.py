"""Structure Break Strategy with Conviction Scoring filter."""
from src.strategies.structure_break import StructureBreakStrategy
from src.strategies.conviction_scorer import ConvictionScorer
import numpy as np


class FilteredStructureBreakStrategy(StructureBreakStrategy):
    min_score = 50

    def init(self):
        super().init()
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

        if not np.isnan(self.swing_h[-1]):
            self._last_sh = self.swing_h[-1]
        if not np.isnan(self.swing_l[-1]):
            self._last_sl = self.swing_l[-1]

        if self._last_sh is None or self._last_sl is None:
            return

        price = self.data.Close[-1]
        prev = self.data.Close[-2] if len(self.data.Close) > 1 else price
        sl_dist = atr_val * self.atr_sl_multiplier
        tp_dist = atr_val * self.atr_tp_multiplier

        ema200_val = self.ema200[-1]
        if np.isnan(ema200_val):
            return

        bar_i = len(self.data.Close) - 1

        if price > self._last_sh and prev <= self._last_sh:
            if price > ema200_val:
                result = self._scorer.score(bar_i, 'long')
                if result['total'] >= self.min_score:
                    if not self.position.is_long:
                        self.position.close()
                        self.buy(sl=price - sl_dist, tp=price + tp_dist)
                        self._last_sh = price

        elif price < self._last_sl and prev >= self._last_sl:
            if price < ema200_val:
                result = self._scorer.score(bar_i, 'short')
                if result['total'] >= self.min_score:
                    if not self.position.is_short:
                        self.position.close()
                        self.sell(sl=price + sl_dist, tp=price - tp_dist)
                        self._last_sl = price
