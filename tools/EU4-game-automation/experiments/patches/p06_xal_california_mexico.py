"""R05: a link with weight 0 in the bookmark state (california -> mexico) gets a steerer (XAL); does it start to propagate?"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402


def patch(t: str) -> str:
    span = sp._entry_span(t, "california", "XAL")
    if span and "has_trader=yes" in t[span[0]:span[1]]:
        t = sp.recall_merchant(t, "XAL", "california")
    return sp.place_merchant(t, "XAL", "california", "steer", "mexico")
