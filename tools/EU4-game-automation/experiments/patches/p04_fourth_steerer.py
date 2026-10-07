"""R09 Q8 / R01: a 4th steering merchant (constantinople -> ragusa); run after the exp_merchants modifier (+1 merchant)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402


def patch(t: str) -> str:
    return sp.place_merchant(t, "VEN", "constantinople", "steer", "ragusa")
