#!/usr/bin/env python3
"""Quick analysis script - current levels, indicators, bias."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from src.data.fetcher import fetch, list_instruments
from src.indicators.technical import ema, rsi, atr, macd, bollinger_bands, support_resistance
from src import load_config


@click.command()
@click.option("--instrument", "-i", default="XAUUSD", help="Instrument name")
@click.option("--interval", "-t", default="1h", help="Timeframe")
def main(instrument, interval):
    """Analyze current market conditions for an instrument."""
    config = load_config()
    click.echo(f"Analyzing {instrument} on {interval}...\n")

    df = fetch(symbol=instrument, interval=interval, period="3mo", config=config)
    close = df["Close"]
    price = close.iloc[-1]

    # Indicators
    ema9 = ema(close, 9).iloc[-1]
    ema21 = ema(close, 21).iloc[-1]
    ema50 = ema(close, 50).iloc[-1]
    rsi_val = rsi(close, 14).iloc[-1]
    atr_val = atr(df, 14).iloc[-1]
    macd_line, signal, hist = macd(close)
    bb_upper, bb_mid, bb_lower = bollinger_bands(close)
    sr = support_resistance(df, lookback=50)

    # Bias
    if ema9 > ema21 > ema50:
        bias = "🟢 BULLISH"
    elif ema9 < ema21 < ema50:
        bias = "🔴 BEARISH"
    else:
        bias = "🟡 NEUTRAL"

    rsi_status = "Overbought" if rsi_val > 70 else "Oversold" if rsi_val < 30 else "Neutral"
    macd_status = "Bullish" if hist.iloc[-1] > 0 else "Bearish"

    click.echo(f"{'Price:':<20} {price:.5f}")
    click.echo(f"{'Bias:':<20} {bias}")
    click.echo(f"{'EMA 9:':<20} {ema9:.5f}")
    click.echo(f"{'EMA 21:':<20} {ema21:.5f}")
    click.echo(f"{'EMA 50:':<20} {ema50:.5f}")
    click.echo(f"{'RSI (14):':<20} {rsi_val:.1f} ({rsi_status})")
    click.echo(f"{'ATR (14):':<20} {atr_val:.5f}")
    click.echo(f"{'MACD Hist:':<20} {hist.iloc[-1]:.5f} ({macd_status})")
    click.echo(f"{'BB Upper:':<20} {bb_upper.iloc[-1]:.5f}")
    click.echo(f"{'BB Lower:':<20} {bb_lower.iloc[-1]:.5f}")
    click.echo(f"\nSupport Levels: {[round(s, 5) for s in sr['support'][:3]]}")
    click.echo(f"Resistance Levels: {[round(r, 5) for r in sr['resistance'][:3]]}")


if __name__ == "__main__":
    main()
