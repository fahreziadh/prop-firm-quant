from src.strategies.ema_cross import EMACrossStrategy
from src.strategies.structure_break import StructureBreakStrategy
from src.strategies.sr_bounce import SRBounceStrategy
from src.strategies.rsi_divergence import RSIDivergenceStrategy
from src.strategies.london_breakout import LondonBreakoutStrategy
from src.strategies.macd_ob import MACDOrderBlockStrategy
from src.strategies.high_conviction import HighConvictionStrategy
from src.strategies.filtered_london_breakout import FilteredLondonBreakoutStrategy
from src.strategies.filtered_structure_break import FilteredStructureBreakStrategy
from src.strategies.sr_break_retest import SRBreakRetestStrategy
from src.strategies.scalp_ema_momentum import ScalpEMAMomentumStrategy
from src.strategies.scalp_sr_quick import ScalpSRQuickStrategy
from src.strategies.scalp_breakout import ScalpBreakoutStrategy
from src.strategies.scalp_session_momentum import ScalpSessionMomentumStrategy

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
    "sr_break_retest": SRBreakRetestStrategy,
    "scalp_ema_momentum": ScalpEMAMomentumStrategy,
    "scalp_sr_quick": ScalpSRQuickStrategy,
    "scalp_breakout": ScalpBreakoutStrategy,
    "scalp_session_momentum": ScalpSessionMomentumStrategy,
}
