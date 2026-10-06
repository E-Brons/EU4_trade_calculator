"""The fixture corpus: manifest, locating saves (raw file or tracked zip), and running verification over all of them.

Worlds are processed one at a time and discarded (a world holds ~50k multipliers); only the VerificationReport is kept.
EU4_FIXTURE_IDS=S14,S42 restricts a run; EU4_TEST_SAVES_DIR points at a directory of raw saves.
"""
from __future__ import annotations

import json
import os
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from app.parsing.tradenodes import load_trade_graph
from app.trade.extract import extract_world
from app.trade.types import World
from app.trade.verify import VerificationReport, verify_world

TESTS_DIR = Path(__file__).resolve().parent.parent.parent / "tests"
FIXTURES_DIR = TESTS_DIR / "fixtures" / "saves"
ZIP_DIR = TESTS_DIR / "fixtures" / "saves_zip"
MANIFEST_PATH = FIXTURES_DIR / "saves.json"


def manifest(path: Path = MANIFEST_PATH) -> list[dict]:
    entries = json.loads(path.read_text(encoding="utf-8"))["saves"]
    for e in entries:
        e.setdefault("kind", "start")
        e.setdefault("expected", "green")
        e.setdefault("covers", [])
    return entries


def selected(entries: list[dict] | None = None) -> list[dict]:
    entries = entries if entries is not None else manifest()
    wanted = os.environ.get("EU4_FIXTURE_IDS")
    if wanted:
        ids = {i.strip() for i in wanted.split(",") if i.strip()}
        entries = [e for e in entries if e["id"] in ids]
    return entries


def locate(entry: dict, tmp_dir: Path, zip_dir: Path = ZIP_DIR, saves_dir: Path | None = None) -> Path | None:
    saves_dir = saves_dir or Path(os.environ.get("EU4_TEST_SAVES_DIR", FIXTURES_DIR))
    raw = saves_dir / entry["file"]
    if raw.exists():
        return raw
    zp = zip_dir / f"{entry['file']}.zip"
    if not zp.exists():
        return None
    with zipfile.ZipFile(zp) as zf:
        zf.extract(entry["file"], path=tmp_dir)
    return tmp_dir / entry["file"]


def iter_worlds(entries: list[dict] | None = None) -> Iterator[tuple[dict, World]]:
    graph = load_trade_graph()
    for entry in selected(entries):
        with tempfile.TemporaryDirectory() as tmp:
            path = locate(entry, Path(tmp))
            if path is None:
                continue
            yield entry, extract_world(path, entry["id"], graph=graph)


@dataclass
class CorpusReport:
    reports: dict[str, VerificationReport]
    entries: dict[str, dict]
    missing: list[str]


def run_corpus(entries: list[dict] | None = None, progress: Callable[[str], None] | None = None) -> CorpusReport:
    chosen = selected(entries)
    reports: dict[str, VerificationReport] = {}
    for entry, world in iter_worlds(chosen):
        reports[entry["id"]] = verify_world(world)
        if progress:
            progress(entry["id"])
    return CorpusReport(reports=reports, entries={e["id"]: e for e in chosen}, missing=[e["id"] for e in chosen if e["id"] not in reports])
