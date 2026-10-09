"""Append one row per verification run to docs/verification_log.md (CI runs this after the tests, pass or fail).

Reads $VERIFY_OUT/stage-report.json (written by the test session). Commit = $GITHUB_SHA or `git rev-parse HEAD`.
Run from backend/:  python scripts/verification_log.py
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.trade import calc  # noqa: E402

LOG = Path(__file__).resolve().parents[2] / "docs" / "verification_log.md"
HEADER = """# Verification log

One row per run of `scripts/verify_all.sh` in CI (appended by `backend/scripts/verification_log.py`, committed by the
`verify-trade-calculation` job). Data: the clean saves of `datasets/eu4/` (reports excluded). Each stage cell is
`not exact / outside 5% / checks`; the CI bar is "outside 5%" = 0 for every stage and every save end to end.

"""


def main() -> int:
    out = Path(os.environ.get("VERIFY_OUT", "verify-out"))
    data = json.loads((out / "stage-report.json").read_text(encoding="utf-8"))
    commit = os.environ.get("GITHUB_SHA") or subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    stages = list(calc.STAGES)
    exact = sum(r["chain"]["status"] == "ok" for r in data.values())
    margin = sum(r["chain"]["status"] != "unknown_variable" and r["chain"].get("margin_failures", 0) == 0 for r in data.values())
    cells = []
    for st in stages:
        rs = [r["stages"][st] for r in data.values()]
        if any(s["status"] == "not_implemented" for s in rs):
            cells.append("n/a")
        else:
            cells.append(f"{sum(s['failures'] for s in rs)} / {sum(s.get('margin_failures', 0) for s in rs)} / {sum(s['checks'] for s in rs)}")
    when = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    row = [when, commit[:8], calc.CALC_VERSION, str(len(data)), f"{exact}", f"{margin}"] + cells
    if not LOG.exists():
        head = ["date (UTC)", "commit", "calc", "saves", "reproduced exactly", "reproduced within 5%"] + stages
        LOG.write_text(HEADER + "| " + " | ".join(head) + " |\n" + "|" + "---|" * len(head) + "\n", encoding="utf-8")
    with LOG.open("a", encoding="utf-8") as f:
        f.write("| " + " | ".join(row) + " |\n")
    print(f"appended to {LOG}: {len(data)} saves, reproduced {margin} within 5% ({exact} exactly)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
