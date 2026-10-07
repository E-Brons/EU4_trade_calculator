"""R11/R05: VEN light-ship fleet -> protect trade at constantinople (VEN passive there)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402,F401


def patch(t: str) -> str:
    return sp.set_light_ship_mission(t, "VEN", "constantinople")
