"""Basic tests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from src.indicators.technical import ema, rsi, atr, macd, bollinger_bands, support_resistance
from src.risk.manager import RiskManager, TradeRecord
from src import load_config


def _sample_df(n=200):
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    return pd.DataFrame({
        "Open": close + np.random.randn(n) * 0.1,
        "High": high, "Low": low, "Close": close,
        "Volume": np.random.randint(1000, 10000, n),
    })


def test_indicators():
    df = _sample_df()
    assert len(ema(df["Close"], 9)) == len(df)
    assert len(rsi(df["Close"], 14)) == len(df)
    assert len(atr(df, 14)) == len(df)
    m, s, h = macd(df["Close"])
    assert len(m) == len(df)
    u, mid, l = bollinger_bands(df["Close"])
    assert len(u) == len(df)
    sr = support_resistance(df)
    assert "support" in sr and "resistance" in sr


def test_risk_manager():
    rm = RiskManager(account_size=100000)
    assert rm.can_trade
    assert rm.equity == 100000
    # Position sizing
    size = rm.position_size(entry=1.1000, stop_loss=1.0950)
    assert size > 0
    # Record winning trade
    rm.record_trade(TradeRecord(1.1, 1.11, "long", size, 500))
    assert rm.equity == 100500
    assert not rm.total_dd_breached
    # Record losing trade
    rm.record_trade(TradeRecord(1.1, 1.09, "long", size, -6000))
    assert rm.daily_drawdown_pct > 0


def test_config():
    config = load_config()
    assert "prop_firm" in config
    assert "instruments" in config
    assert "XAUUSD" in config["instruments"]


if __name__ == "__main__":
    test_indicators()
    print("✅ Indicators OK")
    test_risk_manager()
    print("✅ Risk Manager OK")
    test_config()
    print("✅ Config OK")
    print("\n🎉 All tests passed!")
