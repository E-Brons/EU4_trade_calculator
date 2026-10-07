"""R06 row 2 / R02: VEN's ragusa merchant collects (away from home) instead of steering."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402


def patch(t: str) -> str:
    t = sp.recall_merchant(t, "VEN", "ragusa")
    return sp.place_merchant(t, "VEN", "ragusa", "collect")
