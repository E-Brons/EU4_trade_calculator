"""R01/R10: VEN embargoes RAG (RAG has power at ragusa and venice, where VEN is strong)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402,F401
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r2helpers as h  # noqa: E402


def patch(t: str) -> str:
    return h.add_embargo(t, "VEN", "RAG")
