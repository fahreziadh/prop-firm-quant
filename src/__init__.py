"""Prop Firm Quant Trading Toolkit."""
import os, yaml

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

def load_config(path: str = _CONFIG_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)
