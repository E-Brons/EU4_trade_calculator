"""R02/R09: VEN main trade port -> Zara (4753, ragusa node); capital stays Venezia (112)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402,F401
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r2helpers as h  # noqa: E402


def patch(t: str) -> str:
    return h.set_trade_port(t, "VEN", 4753)
