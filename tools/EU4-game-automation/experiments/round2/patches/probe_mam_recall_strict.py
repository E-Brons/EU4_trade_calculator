"""Probe: recall the MAM aleppo steerer exactly like the game's own recall (Venice series U25 -> U27): drop has_trader,
type and add, keep steer_power, free the envoy, home bonus -0.1 (savepatch.recall_merchant leaves `add`)."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import savepatch as sp  # noqa: E402


def patch(t: str) -> str:
    t = sp.recall_merchant(t, "MAM", "aleppo")
    s, e = sp._entry_span(t, "aleppo", "MAM")
    entry = re.sub(r"\n\t\t\tadd=[\d.]+", "", t[s:e], count=1)
    return t[:s] + entry + t[e:]
