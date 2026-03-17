#!/usr/bin/env python3
"""CLI to run backtests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from src.backtest.engine import run_backtest
from src.analysis.report import format_report
from src.strategies import STRATEGIES


@click.command()
@click.option("--strategy", "-s", type=click.Choice(list(STRATEGIES.keys())), required=True, help="Strategy name")
@click.option("--instrument", "-i", default="XAUUSD", help="Instrument name from config")
@click.option("--period", "-p", default=None, help="Data period (e.g. 6mo, 1y)")
@click.option("--interval", "-t", default="1h", help="Timeframe/interval (e.g. 1h, 4h, 1d)")
@click.option("--plot", is_flag=True, help="Generate HTML plot")
def main(strategy, instrument, period, interval, plot):
    """Run a backtest for a given strategy and instrument."""
    click.echo(f"Running {strategy} on {instrument} ({interval})...")

    try:
        result = run_backtest(
            strategy_name=strategy,
            instrument=instrument,
            period=period,
            interval=interval,
            plot=plot,
        )
        click.echo(format_report(result))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
