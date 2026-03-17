from src.strategies.ema_cross import EMACrossStrategy
from src.strategies.structure_break import StructureBreakStrategy
from src.strategies.sr_bounce import SRBounceStrategy
from src.strategies.rsi_divergence import RSIDivergenceStrategy
from src.strategies.london_breakout import LondonBreakoutStrategy
from src.strategies.macd_ob import MACDOrderBlockStrategy

STRATEGIES = {
    "ema_cross": EMACrossStrategy,
    "structure_break": StructureBreakStrategy,
    "sr_bounce": SRBounceStrategy,
    "rsi_divergence": RSIDivergenceStrategy,
    "london_breakout": LondonBreakoutStrategy,
    "macd_ob": MACDOrderBlockStrategy,
}
