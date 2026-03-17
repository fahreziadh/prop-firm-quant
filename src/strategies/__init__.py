from src.strategies.ema_cross import EMACrossStrategy
from src.strategies.structure_break import StructureBreakStrategy
from src.strategies.sr_bounce import SRBounceStrategy
from src.strategies.rsi_divergence import RSIDivergenceStrategy
from src.strategies.london_breakout import LondonBreakoutStrategy
from src.strategies.macd_ob import MACDOrderBlockStrategy
from src.strategies.high_conviction import HighConvictionStrategy
from src.strategies.filtered_london_breakout import FilteredLondonBreakoutStrategy
from src.strategies.filtered_structure_break import FilteredStructureBreakStrategy

STRATEGIES = {
    "ema_cross": EMACrossStrategy,
    "structure_break": StructureBreakStrategy,
    "sr_bounce": SRBounceStrategy,
    "rsi_divergence": RSIDivergenceStrategy,
    "london_breakout": LondonBreakoutStrategy,
    "macd_ob": MACDOrderBlockStrategy,
    "high_conviction": HighConvictionStrategy,
    "filtered_london_breakout": FilteredLondonBreakoutStrategy,
    "filtered_structure_break": FilteredStructureBreakStrategy,
}
