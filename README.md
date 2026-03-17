# Prop Firm Quant 📈

Quantitative trading toolkit designed for prop firm challenges (FundedNext, FTMO, etc.).

## Features

- **3 Built-in Strategies**: EMA Crossover, Break of Structure (BOS), S/R Bounce
- **Risk Management**: Position sizing, daily/total drawdown tracking, prop firm rule compliance
- **Backtesting Engine**: Powered by backtesting.py with detailed performance reports
- **Technical Indicators**: EMA, RSI, ATR, MACD, Bollinger Bands, Support/Resistance detection
- **Config-Driven**: All parameters in `config.yaml`
- **Free Data**: Uses yfinance (no API key needed)

## Quick Start

```bash
pip install -r requirements.txt

# Run a backtest
python scripts/run_backtest.py -s ema_cross -i XAUUSD -t 1h

# Analyze current market conditions
python scripts/analyze_pair.py -i XAUUSD -t 1h

# Run tests
python tests/test_basic.py
```

## Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `ema_cross` | EMA 9/21 crossover with ATR-based SL/TP | Trending markets |
| `structure_break` | Break of Structure (swing high/low breaks) | Momentum/breakouts |
| `sr_bounce` | Support/Resistance bounce with RSI confirmation | Ranging markets |

## Configuration

Edit `config.yaml` to customize:
- Prop firm rules (account size, drawdown limits, profit target)
- Instrument mappings (yfinance symbols)
- Strategy parameters (periods, multipliers)
- Backtest settings (commission, default period)

## Default Instruments

| Name | yfinance Symbol |
|------|----------------|
| XAUUSD (Gold) | GC=F |
| EURUSD | EURUSD=X |
| GBPUSD | GBPUSD=X |
| NAS100 | NQ=F |

## Risk Management

Default prop firm rules (FundedNext):
- **Max Daily Drawdown**: 5%
- **Max Total Drawdown**: 10%
- **Risk Per Trade**: 1%
- **Profit Target**: 10%

## License

MIT
