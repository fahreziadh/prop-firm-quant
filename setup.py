from setuptools import setup, find_packages

setup(
    name="prop-firm-quant",
    version="1.0.0",
    description="Quantitative trading toolkit for prop firm challenges",
    author="Fahrezi Adha",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "yfinance>=0.2.31",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "backtesting>=0.3.3",
        "PyYAML>=6.0",
        "matplotlib>=3.7.0",
        "ta>=0.10.2",
        "click>=8.1.0",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "pfq-backtest=scripts.run_backtest:main",
            "pfq-analyze=scripts.analyze_pair:main",
        ],
    },
)
