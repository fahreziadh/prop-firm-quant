"""Abstract base strategy for backtesting.py integration."""
from backtesting import Strategy
from abc import abstractmethod


class BaseStrategy(Strategy):
    """Base strategy with common utilities."""

    atr_period = 14
    atr_sl_multiplier = 1.5
    atr_tp_multiplier = 3.0
    risk_pct = 1.0  # % of equity to risk per trade

    def calc_position_size(self, sl_distance: float) -> float:
        """Calculate position size based on risk percentage and SL distance."""
        if sl_distance <= 0:
            return 0
        risk_amount = self.equity * (self.risk_pct / 100)
        size = risk_amount / sl_distance
        return max(size, 0)
