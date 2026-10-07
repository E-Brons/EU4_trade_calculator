"""TUR (home constantinople, non-terminal): recall the home merchant."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import savepatch as sp  # noqa: E402


def patch(t: str) -> str:
    return sp.recall_merchant(t, "TUR", "constantinople")
