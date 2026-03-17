"""Backtesting engine wrapping backtesting.py."""
import pandas as pd
from backtesting import Backtest
from src import load_config
from src.data.fetcher import fetch
from src.strategies import STRATEGIES
from src.analysis.report import generate_report


def run_backtest(
    strategy_name: str,
    instrument: str = None,
    yf_symbol: str = None,
    period: str = None,
    interval: str = "1h",
    cash: float = None,
    commission: float = None,
    config: dict = None,
    strategy_params: dict = None,
    plot: bool = False,
) -> dict:
    """Run a backtest and return results dict."""
    if config is None:
        config = load_config()

    if cash is None:
        cash = config["prop_firm"]["account_size"]
    if commission is None:
        commission = config["backtest"]["commission"]
    if period is None:
        period = config["backtest"]["default_period"]

    # Get strategy class
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(STRATEGIES.keys())}")
    strategy_cls = STRATEGIES[strategy_name]

    # Fetch data
    df = fetch(symbol=instrument, yf_symbol=yf_symbol, period=period, interval=interval, config=config)

    # Merge config params with overrides
    params = {}
    strat_config = config.get("strategies", {}).get(strategy_name, {})
    params.update(strat_config)
    if strategy_params:
        params.update(strategy_params)

    # Run backtest
    bt = Backtest(df, strategy_cls, cash=cash, commission=commission, exclusive_orders=True)
    stats = bt.run(**params)

    result = generate_report(stats, strategy_name, instrument or yf_symbol)

    if plot:
        bt.plot(open_browser=False, filename=f"backtest_{strategy_name}_{instrument or 'custom'}.html")
        result["plot_file"] = f"backtest_{strategy_name}_{instrument or 'custom'}.html"

    return result
