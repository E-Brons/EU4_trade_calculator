#!/usr/bin/env python3
"""Offline checks for round 2: jobs parse, referenced files exist (diversity bases may not exist yet), effect keywords
exist in the game (scripts or, for engine-only effects, the binary), every patch runs on its real base save and
changes what it should. Run from anywhere."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAME = Path.home() / "Library/Application Support/Steam/steamapps/common/Europa Universalis IV"
BIN_STRINGS = Path("/tmp/eu4_strings.txt")  # `strings -a -n 3 eu4.app/Contents/MacOS/eu4`
sys.path.insert(0, str(HERE.parents[1]))

ENGINE_ONLY = {"add_idea", "add_idea_group", "add_to_trade_company"}  # in the binary, no vanilla script uses them


def script_keywords() -> set[str]:
    kw: set[str] = set()
    for d in ("common", "events", "decisions", "missions"):
        for f in (GAME / d).rglob("*.txt"):
            kw.update(re.findall(r"\b([a-z_]+)\s*=", f.read_text(encoding="latin-1", errors="replace")))
    return kw


def main() -> int:
    bad = 0
    kw = script_keywords()
    binary = set(BIN_STRINGS.read_text(errors="replace").split("\n")) if BIN_STRINGS.exists() else set()
    texts: dict[str, str] = {}
    for job in sorted((HERE / "jobs").glob("*.json")):
        spec = json.loads(job.read_text())
        base = spec.get("base_save")
        if base:
            bp = (job.parent / base).resolve()
            if not bp.exists():
                print(f"{job.stem}: base {base} not there yet" + (" (diversity batch)" if "diversity" in base else " MISSING"))
                bad += "diversity" not in base
        for step in spec["script"]:
            for key in ("effects", "patch", "console_commands"):
                if key in step and not (job.parent / step[key]).exists():
                    print(f"{job.stem}: {key} {step[key]} MISSING"); bad += 1
            if "effects" in step:
                words = set(re.findall(r"\b([a-z_]+)\s*=", (job.parent / step["effects"]).read_text()))
                for w in words:
                    if w in kw or (w in ENGINE_ONLY and w in binary):
                        continue
                    print(f"{job.stem}: effect keyword {w!r} not found in game scripts/binary"); bad += 1
            if "patch" in step and base and (job.parent / base).exists():
                bp = str((job.parent / base).resolve())
                if bp not in texts:
                    texts[bp] = open(bp, encoding="latin-1").read()
                spec_ = importlib.util.spec_from_file_location(job.stem, job.parent / step["patch"])
                mod = importlib.util.module_from_spec(spec_)
                spec_.loader.exec_module(mod)
                try:
                    out = mod.patch(texts[bp])
                    import subprocess, tempfile
                    with tempfile.NamedTemporaryFile("w", suffix=".eu4", delete=False, encoding="latin-1") as fh:
                        fh.write(out)
                    d = subprocess.run(["diff", bp, fh.name], capture_output=True, text=True, encoding="latin-1").stdout
                    Path(fh.name).unlink()
                    changed = [ln for ln in d.splitlines() if ln[:2] in ("< ", "> ")]
                    print(f"{job.stem}: patch ok, {len(changed)} diff lines: {[c.strip()[:60] for c in changed[:6]]}")
                except Exception as e:  # noqa: BLE001
                    print(f"{job.stem}: patch FAILED {type(e).__name__}: {e}"); bad += 1
    order = (HERE / "ORDER.txt").read_text().split()
    jobs = sorted(p.stem for p in (HERE / "jobs").glob("*.json"))
    if sorted(order) != jobs:
        print("ORDER.txt does not match jobs/"); bad += 1
    print("OK" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
