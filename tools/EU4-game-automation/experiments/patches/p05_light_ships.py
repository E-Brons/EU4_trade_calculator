"""R05 / R11: move VEN's light-ship-only fleet from its current protect node to another node (first one accepted)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402

CANDIDATES = ("ragusa", "constantinople", "venice", "genua", "tunis")


def patch(t: str) -> str:
    for node in CANDIDATES:
        try:
            out = sp.set_light_ship_mission(t, "VEN", node)
            print("light ships ->", node, flush=True)
            return out
        except sp.PatchError as e:
            print("light ships", node, "refused:", e, flush=True)
    raise sp.PatchError("no candidate node accepted the fleet")
