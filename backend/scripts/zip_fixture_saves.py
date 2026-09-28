#!/usr/bin/env python3
"""Compresses the real .eu4 fixture saves for git tracking.

The raw saves (`tests/fixtures/saves/*.eu4`, ~2.8GB total) stay gitignored
-- too large and too incompressible-as-a-single-blob to track directly.
Each one compresses ~13x on its own (plain Clausewitz text), so instead we
track a small single-file zip per save in `tests/fixtures/saves_zip/`,
comfortably under any host's per-file size limit even though the originals
aren't. `tests/test_real_saves.py` unzips one at a time, on demand, into
pytest's per-test `tmp_path` when the raw file isn't already present --
see its `_save_path()`.

Usage:
    python3 scripts/zip_fixture_saves.py          # (re-)zip every save
    python3 scripts/zip_fixture_saves.py S51 S52  # just these ids
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "saves"
ZIP_DIR = FIXTURES_DIR.parent / "saves_zip"
MANIFEST_PATH = FIXTURES_DIR / "saves.json"


def main() -> None:
    wanted_ids = set(sys.argv[1:]) or None
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ZIP_DIR.mkdir(exist_ok=True)

    zipped = skipped = 0
    for entry in manifest["saves"]:
        if wanted_ids and entry["id"] not in wanted_ids:
            continue
        src = FIXTURES_DIR / entry["file"]
        if not src.exists():
            skipped += 1
            continue
        dest = ZIP_DIR / f"{entry['file']}.zip"
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.write(src, arcname=entry["file"])
        zipped += 1
        print(f"{entry['id']}: {src.stat().st_size:,}B -> {dest.stat().st_size:,}B")

    print(f"\nzipped {zipped}, skipped {skipped} (no raw file present)")


if __name__ == "__main__":
    main()
