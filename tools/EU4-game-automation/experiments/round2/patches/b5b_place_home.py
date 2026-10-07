"""R07 B5b (base U10, no home merchant): VEN's alexandria merchant moved to venice (collect at home)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402,F401


def patch(t: str) -> str:
    return sp.place_merchant(sp.recall_merchant(t, "VEN", "alexandria"), "VEN", "venice", "collect")
