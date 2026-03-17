from src.strategies.ema_cross import EMACrossStrategy
from src.strategies.structure_break import StructureBreakStrategy
from src.strategies.sr_bounce import SRBounceStrategy

STRATEGIES = {
    "ema_cross": EMACrossStrategy,
    "structure_break": StructureBreakStrategy,
    "sr_bounce": SRBounceStrategy,
}
