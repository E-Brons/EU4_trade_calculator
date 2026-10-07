"""R07/R01 (base U10): recall only the alexandria steerer (separates B5b's two parts)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402,F401


def patch(t: str) -> str:
    return sp.recall_merchant(t, "VEN", "alexandria")
