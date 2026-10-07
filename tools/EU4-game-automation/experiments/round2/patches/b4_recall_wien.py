"""R01/R09: recall VEN's wien steerer (direct link into the home node)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402,F401


def patch(t: str) -> str:
    return sp.recall_merchant(t, "VEN", "wien")
