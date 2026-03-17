"""Performance analysis and reporting."""
import numpy as np


def generate_report(stats, strategy_name: str, instrument: str) -> dict:
    """Extract key metrics from backtesting.py stats object."""
    equity_curve = stats.get("_equity_curve", None)
    trades = stats.get("_trades", None)

    report = {
        "strategy": strategy_name,
        "instrument": instrument,
        "start": str(stats.get("Start", "")),
        "end": str(stats.get("End", "")),
        "duration": str(stats.get("Duration", "")),
        "initial_equity": stats.get("Start", 0),
        "final_equity": round(float(stats.get("Equity Final [$]", 0)), 2),
        "equity_peak": round(float(stats.get("Equity Peak [$]", 0)), 2),
        "return_pct": round(float(stats.get("Return [%]", 0)), 2),
        "max_drawdown_pct": round(float(stats.get("Max. Drawdown [%]", 0)), 2),
        "sharpe_ratio": round(float(stats.get("Sharpe Ratio", 0) or 0), 3),
        "sortino_ratio": round(float(stats.get("Sortino Ratio", 0) or 0), 3),
        "calmar_ratio": round(float(stats.get("Calmar Ratio", 0) or 0), 3),
        "win_rate_pct": round(float(stats.get("Win Rate [%]", 0) or 0), 1),
        "profit_factor": round(float(stats.get("Profit Factor", 0) or 0), 2),
        "total_trades": int(stats.get("# Trades", 0)),
        "avg_trade_pct": round(float(stats.get("Avg. Trade [%]", 0) or 0), 2),
        "best_trade_pct": round(float(stats.get("Best Trade [%]", 0) or 0), 2),
        "worst_trade_pct": round(float(stats.get("Worst Trade [%]", 0) or 0), 2),
        "max_trade_duration": str(stats.get("Max. Trade Duration", "")),
        "avg_trade_duration": str(stats.get("Avg. Trade Duration", "")),
        "exposure_pct": round(float(stats.get("Exposure Time [%]", 0) or 0), 1),
    }

    # R-multiples if we have trade data
    if trades is not None and len(trades) > 0:
        pnls = trades["PnL"].values
        if len(pnls) > 0:
            avg_win = np.mean(pnls[pnls > 0]) if np.any(pnls > 0) else 0
            avg_loss = abs(np.mean(pnls[pnls < 0])) if np.any(pnls < 0) else 1
            report["avg_r_multiple"] = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0

    return report


def format_report(report: dict) -> str:
    """Pretty print a report dict."""
    lines = [
        f"═══ Backtest Report: {report['strategy']} on {report['instrument']} ═══",
        f"Period: {report['start']} → {report['end']}",
        f"",
        f"{'Return:':<25} {report['return_pct']:>8}%",
        f"{'Final Equity:':<25} ${report['final_equity']:>12,.2f}",
        f"{'Max Drawdown:':<25} {report['max_drawdown_pct']:>8}%",
        f"{'Sharpe Ratio:':<25} {report['sharpe_ratio']:>8}",
        f"{'Sortino Ratio:':<25} {report['sortino_ratio']:>8}",
        f"{'Profit Factor:':<25} {report['profit_factor']:>8}",
        f"",
        f"{'Total Trades:':<25} {report['total_trades']:>8}",
        f"{'Win Rate:':<25} {report['win_rate_pct']:>8}%",
        f"{'Avg Trade:':<25} {report['avg_trade_pct']:>8}%",
        f"{'Best Trade:':<25} {report['best_trade_pct']:>8}%",
        f"{'Worst Trade:':<25} {report['worst_trade_pct']:>8}%",
        f"{'Avg R-Multiple:':<25} {report.get('avg_r_multiple', 'N/A'):>8}",
        f"{'Exposure:':<25} {report['exposure_pct']:>8}%",
    ]
    return "\n".join(lines)
