"""The research datasets: locating clean saves and running verification over them.

Layout (docs/trade_testing.md):  datasets/eu4/<game version>/<mods key>/<dlc key>/<series>/series.json + <file>.zip
Every series.json lists its saves (id, file, tag, date, role, change, covers, sha256, quality). Series of kind
"report" hold saves users submitted from the app; they are verified and logged but do not gate the calculation.

Worlds are processed one at a time and discarded (a world holds ~50k multipliers); only the VerificationReport is kept.
EU4_FIXTURE_IDS=U10,U27 restricts a run to those saves; EU4_SERIES=venice-1444 to those series.
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
from app.trade import calc
from app.trade.extract import extract_world
from app.trade.types import World
from app.trade.verify import VerificationReport, verify_world

REPO_DIR = Path(__file__).resolve().parents[3]
DATASETS_DIR = REPO_DIR / "datasets" / "eu4"
REPORT_KIND = "report"


def dataset_dir(game_version: str, mods_key: str, dlc_key: str, root: Path = DATASETS_DIR) -> Path:
    return root / game_version / mods_key / dlc_key


def manifest(root: Path = DATASETS_DIR, game_version: str = calc.SUPPORTED_GAME_VERSION) -> list[dict]:
    """Every save of every series of the given game version, with its series, kind, dataset and zip path."""
    entries: list[dict] = []
    for series_path in sorted((root / game_version).glob("*/*/*/series.json")):
        series = json.loads(series_path.read_text(encoding="utf-8"))
        for e in series["saves"]:
            entries.append(e | {
                "series": series["series"], "kind": series.get("kind", "observation"),
                "dataset": str(series_path.parent.parent.relative_to(root)), "zip": str(series_path.parent / f"{e['file']}.zip"),
                "covers": e.get("covers", []),
            })
    return entries


def selected(entries: list[dict] | None = None, include_reports: bool = False) -> list[dict]:
    entries = entries if entries is not None else manifest()
    if not include_reports:
        entries = [e for e in entries if e["kind"] != REPORT_KIND]
    ids = {i.strip() for i in os.environ.get("EU4_FIXTURE_IDS", "").split(",") if i.strip()}
    series = {s.strip() for s in os.environ.get("EU4_SERIES", "").split(",") if s.strip()}
    return [e for e in entries if (not ids or e["id"] in ids) and (not series or e["series"] in series)]


def locate(entry: dict, tmp_dir: Path) -> Path | None:
    """Extract the save from its zip into tmp_dir; None if the zip is missing (or only an LFS pointer was checked out)."""
    zp = Path(entry["zip"])
    if not zp.exists() or not zipfile.is_zipfile(zp):
        return None
    with zipfile.ZipFile(zp) as zf:
        zf.extract(entry["file"], path=tmp_dir)
    return tmp_dir / entry["file"]


def iter_worlds(entries: list[dict]) -> Iterator[tuple[dict, World]]:
    graph = load_trade_graph()
    for entry in entries:
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
    chosen = entries if entries is not None else selected()
    reports: dict[str, VerificationReport] = {}
    for entry, world in iter_worlds(chosen):
        reports[entry["id"]] = verify_world(world)
        if progress:
            progress(entry["id"])
    return CorpusReport(reports=reports, entries={e["id"]: e for e in chosen}, missing=[e["id"] for e in chosen if e["id"] not in reports])
