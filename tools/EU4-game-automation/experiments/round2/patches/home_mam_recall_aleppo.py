"""MAM (home alexandria, non-terminal): recall the aleppo steerer (home bonus from a steerer, non-end home node)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import savepatch as sp  # noqa: E402


def patch(t: str) -> str:
    return sp.recall_merchant(t, "MAM", "aleppo")
