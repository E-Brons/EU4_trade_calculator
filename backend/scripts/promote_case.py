"""Manage stored user cases (Uxx fixtures).

  python3 scripts/promote_case.py --list                 show every stored case, its expected status and its current result
  python3 scripts/promote_case.py --check                validate files/naming/hash of every case (no calculation)
  python3 scripts/promote_case.py U03 --green            flip a case to expected=green, only if it now verifies
Run from backend/. The server never commits; you commit the zip (git LFS) and saves.json yourself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.parsing.tradenodes import load_trade_graph  # noqa: E402
from app.trade import corpus  # noqa: E402
from app.trade.extract import extract_world  # noqa: E402
from app.trade.verify import verify_world  # noqa: E402

NAME = re.compile(r"^U\d{2,}_[A-Z0-9]{2,4}\.\d{4}\.\d{2}\.\d{2}\.eu4$")


def user_cases() -> list[dict]:
    return [e for e in corpus.manifest() if e["kind"] == "user_case"]


def check() -> int:
    bad = 0
    for e in user_cases():
        problems = []
        if not NAME.match(e["file"]):
            problems.append("file name does not match Uxx_TAG.yyyy.mm.dd.eu4")
        zp = corpus.ZIP_DIR / f"{e['file']}.zip"
        if not zp.exists():
            problems.append("zip missing (git lfs pull?)")
        else:
            import zipfile
            with zipfile.ZipFile(zp) as zf:
                body = zf.read(e["file"])
            if hashlib.sha256(body).hexdigest() != e.get("sha256"):
                problems.append("sha256 does not match manifest")
        print(f"{e['id']}: {'OK' if not problems else '; '.join(problems)}")
        bad += bool(problems)
    return 1 if bad else 0


def result(e: dict):
    with tempfile.TemporaryDirectory() as tmp:
        path = corpus.locate(e, Path(tmp))
        return verify_world(extract_world(path, e["id"], graph=load_trade_graph()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("case", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--green", action="store_true")
    a = ap.parse_args()
    if a.check:
        return check()
    if a.list or not a.case:
        for e in user_cases():
            r = result(e)
            print(f"{e['id']} {e['tag']} {e['date']} expected={e['expected']} now={r.status} first_failing_stage={r.first_failing_stage}")
        return 0
    entry = next((e for e in user_cases() if e["id"] == a.case), None)
    if entry is None:
        print(f"no such user case: {a.case}")
        return 2
    r = result(entry)
    if not a.green:
        print(f"{entry['id']}: {r.status}, first failing stage {r.first_failing_stage}")
        return 0
    if r.status != "verified":
        print(f"{entry['id']} still fails ({r.first_failing_stage}); not promoting")
        return 1
    data = json.loads(corpus.MANIFEST_PATH.read_text(encoding="utf-8"))
    for e in data["saves"]:
        if e["id"] == entry["id"]:
            e["expected"] = "green"
    corpus.MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"{entry['id']} is now expected green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
