"""R08: VEN's ragusa merchant steers to genua (index 2) instead of venice (index 1); nothing else changes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402


def patch(t: str) -> str:
    t = sp.recall_merchant(t, "VEN", "ragusa")
    return sp.place_merchant(t, "VEN", "ragusa", "steer", "genua")
