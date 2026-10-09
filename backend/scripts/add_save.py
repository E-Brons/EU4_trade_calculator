"""Add one save to a research dataset (protocol: docs/research/experiments.md). Run from backend/.

  python scripts/add_save.py <save.eu4> --series exp-core-1444 --role B3 --change "wien merchant: steer venice -> saxony" [--covers IV-04]

Rejects the save (and says why) unless it is clean and fits its series; see app/trade/intake.py. Never commits:
`git add` the new zip (LFS) and series.json yourself.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.trade import intake  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("save", type=Path)
    ap.add_argument("--series", required=True)
    ap.add_argument("--role", required=True, help="observation | A | C | C' | B<n>")
    ap.add_argument("--change", default="", help="the one change of a B save, in one line")
    ap.add_argument("--covers", default="", help="edge-case ids it exercises, comma separated (e.g. IV-04)")
    ap.add_argument("--description", default="", help="series description (first save of a new series)")
    ap.add_argument("--reloaded", action="store_true", help="the save was made by reloading the series' A (EU4 then draws a new seed)")
    a = ap.parse_args()
    try:
        added = intake.add_save(a.save, a.series, a.role, a.change, [c.strip() for c in a.covers.split(",") if c.strip()], a.description,
                                reloaded=a.reloaded)
    except intake.Rejected as e:
        print(f"REJECTED: {e}")
        return 1
    print(f"added {added.id} -> {added.series_dir / (added.file + '.zip')}")
    if added.placements_changed:
        print("placements changed vs A at:", ", ".join(added.placements_changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
