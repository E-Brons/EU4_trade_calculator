"""MAM: the aleppo merchant moves home and collects at alexandria (vs home_mam_recall_aleppo: effect of a home merchant)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import savepatch as sp  # noqa: E402


def patch(t: str) -> str:
    return sp.place_merchant(sp.recall_merchant(t, "MAM", "aleppo"), "MAM", "alexandria", "collect")
