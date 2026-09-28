#!/usr/bin/env python3
"""Background watcher for docs/test.md sections B+C (manifest IDs S36-S50).

Polls the EU4 "save games" folder, and whenever a new .eu4 shows up that
matches a still-missing section-B/C manifest entry (matched by exact
(tag, date) -- there are real collisions on date alone within these two
sections, e.g. five different S## entries all start at 1550.1.1, so date
alone isn't enough), copies it into tests/fixtures/saves/ under the
correct manifest filename.

Anything that parses fine but doesn't match any pending entry (tag was a
wrong guess in the manifest, wrong bookmark, etc.) gets staged in
tests/fixtures/saves/_unmatched/ instead of silently dropped, for manual
reconciliation later (same workflow used for section A's tag corrections).

Stop it by creating tests/fixtures/saves/.stop_collecting (Claude does
this when you say you're done) -- it finishes the current pass and exits
cleanly rather than being killed mid-copy.

Usage:
    python3 scripts/collect_new_saves.py
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.parsing.save import load_save

SRC_DIR = Path(
    "/Users/elkanabronstein/Documents/Paradox Interactive/Europa Universalis IV/save games"
)
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "saves"
MANIFEST_PATH = FIXTURES_DIR / "saves.json"
UNMATCHED_DIR = FIXTURES_DIR / "_unmatched"
STOP_FILE = FIXTURES_DIR / ".stop_collecting"
LOG_FILE = FIXTURES_DIR / "_collect_log.txt"

TARGET_IDS = {f"S{n}" for n in range(36, 51)}  # section B (36-42) + section C (43-50)
POLL_SECONDS = 15


def log(msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def already_collected_keys(manifest: dict) -> set[tuple[str, str]]:
    """(tag, date) pairs for every manifest entry whose fixture file already
    exists -- from ANY section, not just B/C, so we don't re-stage the
    section-A saves already sitting in the same source folder."""
    keys = set()
    for e in manifest["saves"]:
        if (FIXTURES_DIR / e["file"]).exists():
            keys.add((e["tag"], e["date"]))
    return keys


def pending_bc_entries(manifest: dict) -> list[dict]:
    return [
        e
        for e in manifest["saves"]
        if e["id"] in TARGET_IDS and not (FIXTURES_DIR / e["file"]).exists()
    ]


def main() -> None:
    UNMATCHED_DIR.mkdir(exist_ok=True)
    seen: set[tuple[str, float, int]] = set()
    log(f"collector started, watching {SRC_DIR}")
    log(f"targeting manifest ids {sorted(TARGET_IDS, key=lambda s: int(s[1:]))}")

    while True:
        if STOP_FILE.exists():
            log("stop file seen -- exiting")
            STOP_FILE.unlink()
            break

        manifest = load_manifest()
        pending = pending_bc_entries(manifest)
        if not pending:
            log("all section B+C saves already collected -- nothing left to watch for, exiting")
            break
        done_keys = already_collected_keys(manifest)

        for path in sorted(SRC_DIR.glob("*.eu4")):
            if "ironman" in path.name.lower():
                continue  # explicitly out of scope, see conversation history
            try:
                stat = path.stat()
            except OSError:
                continue
            key = (path.name, stat.st_mtime, stat.st_size)
            if key in seen:
                continue
            seen.add(key)

            try:
                parsed = load_save(path)
            except Exception as exc:  # noqa: BLE001 -- best-effort background scan
                log(f"SKIP {path.name}: failed to parse ({exc})")
                continue

            ident = (parsed.player_tag, parsed.date)
            if ident in done_keys:
                continue  # already have this one (section A, or already collected B/C)

            match = next(
                (e for e in pending if e["tag"] == parsed.player_tag and e["date"] == parsed.date),
                None,
            )
            if match:
                dest = FIXTURES_DIR / match["file"]
                shutil.copy2(path, dest)
                log(f"MATCHED {path.name} -> {match['id']} ({match['tag']} {match['date']})")
                pending.remove(match)
                done_keys.add(ident)
            else:
                dest = UNMATCHED_DIR / f"{parsed.player_tag}_{parsed.date}_{path.name}"
                if not dest.exists():
                    shutil.copy2(path, dest)
                    log(
                        f"UNMATCHED {path.name}: tag={parsed.player_tag} date={parsed.date} "
                        f"doesn't match any pending B/C slot -- staged at {dest.relative_to(FIXTURES_DIR)}"
                    )

        time.sleep(POLL_SECONDS)

    log("collector stopped")


if __name__ == "__main__":
    main()
