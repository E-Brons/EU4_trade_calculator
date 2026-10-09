"""Validate every research dataset without running the calculation (scripts/verify_all.sh runs this first).

Per save: file name pattern, unique id, the zip exists and is a real zip (not an LFS pointer: run `git lfs pull`), one
member named like the file, sha256 of the member matches series.json, and - outside `reports` - the recorded quality is
clean. Per dataset: dataset.json exists and its version / mods / DLC keys match the folder names.
Run from backend/.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.trade import corpus  # noqa: E402

NAME = re.compile(r"^U\d{2,}_[A-Z0-9]{2,4}\.\d{4}\.\d{2}\.\d{2}\.eu4$")


def problems() -> list[str]:
    out: list[str] = []
    for ds in sorted(corpus.DATASETS_DIR.glob("*/*/*/dataset.json")):
        meta = json.loads(ds.read_text(encoding="utf-8"))
        version, mods, dlc = ds.parent.relative_to(corpus.DATASETS_DIR).parts
        if (meta.get("game_version"), meta.get("mods_key"), meta.get("dlc_key")) != (version, mods, dlc):
            out.append(f"{ds}: keys do not match the folder names")
    ids: dict[str, str] = {}
    for version_dir in sorted(p for p in corpus.DATASETS_DIR.iterdir() if p.is_dir()):
        for e in corpus.manifest(game_version=version_dir.name):
            where = f"{e['dataset']}/{e['series']}/{e['id']}"
            if e["id"] in ids:
                out.append(f"{where}: id also used in {ids[e['id']]}")
            ids[e["id"]] = where
            if not NAME.match(e["file"]):
                out.append(f"{where}: file name does not match Uxx_TAG.yyyy.mm.dd.eu4")
            zp = Path(e["zip"])
            if not zp.exists() or not zipfile.is_zipfile(zp):
                out.append(f"{where}: zip missing or an LFS pointer (git lfs pull?)")
                continue
            with zipfile.ZipFile(zp) as zf:
                if zf.namelist() != [e["file"]]:
                    out.append(f"{where}: zip members {zf.namelist()} != [{e['file']}]")
                    continue
                digest = hashlib.sha256(zf.read(e["file"])).hexdigest()
            if e.get("sha256") and digest != e["sha256"]:
                out.append(f"{where}: sha256 mismatch")
            q = e.get("quality", {})
            if e["kind"] != corpus.REPORT_KIND and (q.get("timing") != "tick_day" or q.get("own_merchants_in_transit") or q.get("own_fleets_in_transit")):
                out.append(f"{where}: not a clean save ({q})")
    return out


if __name__ == "__main__":
    found = problems()
    for p in found:
        print("PROBLEM", p)
    print(f"datasets: {len(found)} problem(s)")
    sys.exit(1 if found else 0)
