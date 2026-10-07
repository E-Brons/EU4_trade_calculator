"""R04: add transfer_trade_power MAN -> VEN amount=1.000 (is_enforced) on 1444.12.1."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402,F401
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r2helpers as h  # noqa: E402


def patch(t: str) -> str:
    return h.add_transfer(t, "MAN", "VEN", 1.0, "1444.12.1")
