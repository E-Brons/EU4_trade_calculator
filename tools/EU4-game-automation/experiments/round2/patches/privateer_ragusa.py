"""R10 (experimental): VEN light-ship fleet privateering at ragusa (mission key renamed)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402,F401
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r2helpers as h  # noqa: E402


def patch(t: str) -> str:
    return h.privateer(t, "VEN", "ragusa")
