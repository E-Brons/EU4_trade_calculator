"""Prints how the trade calculation does against every fixture save, stage by stage (the RED -> GREEN dashboard).

Usage (from backend/):  python3 scripts/stage_report.py [--ids S14,S42] [--json out.json] [--markdown out.md]
Exit status 0 always: this is a report; tests/trade decide pass/fail.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.trade import corpus, report  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids")
    ap.add_argument("--json")
    ap.add_argument("--markdown")
    a = ap.parse_args()
    if a.ids:
        os.environ["EU4_FIXTURE_IDS"] = a.ids
    result = corpus.run_corpus(progress=lambda sid: print(f"  {sid}", end="", flush=True))
    print()
    text = report.markdown(result)
    print(text)
    if a.markdown:
        Path(a.markdown).write_text(text, encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps({k: v.to_dict() for k, v in result.reports.items()}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
