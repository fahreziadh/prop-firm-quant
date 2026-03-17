"""Data fetching via yfinance."""
import yfinance as yf
import pandas as pd
from src import load_config


def fetch(symbol: str = None, yf_symbol: str = None, period: str = "6mo",
          interval: str = "1h", config: dict = None) -> pd.DataFrame:
    """Fetch OHLCV data. Pass either a config instrument name or a raw yfinance symbol."""
    if config is None:
        config = load_config()

    if yf_symbol is None:
        instruments = config.get("instruments", {})
        if symbol and symbol in instruments:
            yf_symbol = instruments[symbol]["yfinance_symbol"]
        else:
            yf_symbol = symbol  # try as-is

    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No data returned for {yf_symbol}")
    # Normalize columns
    df = df.rename(columns={c: c.capitalize() for c in df.columns})
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col not in df.columns:
            raise ValueError(f"Missing column {col}")
    return df[["Open", "High", "Low", "Close", "Volume"]]


def list_instruments(config: dict = None) -> dict:
    if config is None:
        config = load_config()
    return config.get("instruments", {})
