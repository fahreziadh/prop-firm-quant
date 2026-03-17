"""Risk management module for prop firm rules."""
from dataclasses import dataclass, field
from typing import List
from src import load_config


@dataclass
class TradeRecord:
    entry_price: float
    exit_price: float
    direction: str  # "long" or "short"
    size: float
    pnl: float
    date: str = ""


@dataclass
class RiskManager:
    """Tracks risk metrics against prop firm rules."""
    account_size: float = 100000
    max_daily_dd_pct: float = 5.0
    max_total_dd_pct: float = 10.0
    risk_per_trade_pct: float = 1.0
    profit_target_pct: float = 10.0

    equity: float = 0
    peak_equity: float = 0
    daily_start_equity: float = 0
    trades: List[TradeRecord] = field(default_factory=list)

    def __post_init__(self):
        if self.equity == 0:
            self.equity = self.account_size
        if self.peak_equity == 0:
            self.peak_equity = self.equity
        if self.daily_start_equity == 0:
            self.daily_start_equity = self.equity

    @classmethod
    def from_config(cls, config: dict = None):
        if config is None:
            config = load_config()
        pf = config["prop_firm"]
        return cls(
            account_size=pf["account_size"],
            max_daily_dd_pct=pf["max_daily_drawdown_pct"],
            max_total_dd_pct=pf["max_total_drawdown_pct"],
            risk_per_trade_pct=pf["risk_per_trade_pct"],
            profit_target_pct=pf["profit_target_pct"],
        )

    def new_day(self):
        self.daily_start_equity = self.equity

    def position_size(self, entry: float, stop_loss: float) -> float:
        """Calculate position size based on risk per trade."""
        sl_distance = abs(entry - stop_loss)
        if sl_distance == 0:
            return 0
        risk_amount = self.equity * (self.risk_per_trade_pct / 100)
        return risk_amount / sl_distance

    def record_trade(self, trade: TradeRecord):
        self.trades.append(trade)
        self.equity += trade.pnl
        self.peak_equity = max(self.peak_equity, self.equity)

    @property
    def total_drawdown_pct(self) -> float:
        if self.peak_equity == 0:
            return 0
        return ((self.peak_equity - self.equity) / self.peak_equity) * 100

    @property
    def daily_drawdown_pct(self) -> float:
        if self.daily_start_equity == 0:
            return 0
        return ((self.daily_start_equity - self.equity) / self.daily_start_equity) * 100

    @property
    def daily_dd_breached(self) -> bool:
        return self.daily_drawdown_pct >= self.max_daily_dd_pct

    @property
    def total_dd_breached(self) -> bool:
        return self.total_drawdown_pct >= self.max_total_dd_pct

    @property
    def target_reached(self) -> bool:
        profit_pct = ((self.equity - self.account_size) / self.account_size) * 100
        return profit_pct >= self.profit_target_pct

    @property
    def can_trade(self) -> bool:
        return not self.daily_dd_breached and not self.total_dd_breached

    def status(self) -> dict:
        return {
            "equity": round(self.equity, 2),
            "peak_equity": round(self.peak_equity, 2),
            "total_drawdown_pct": round(self.total_drawdown_pct, 2),
            "daily_drawdown_pct": round(self.daily_drawdown_pct, 2),
            "daily_dd_breached": self.daily_dd_breached,
            "total_dd_breached": self.total_dd_breached,
            "target_reached": self.target_reached,
            "can_trade": self.can_trade,
            "total_trades": len(self.trades),
        }
