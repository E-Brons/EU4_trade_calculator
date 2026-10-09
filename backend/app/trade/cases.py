"""Stores user-submitted saves (the app's "store this save for future enhancement") for later investigation.

A stored save is the flat save text zipped into the `reports` series of the dataset that matches the save's game version,
mod list and DLC set: datasets/eu4/<version>/<mods key>/<dlc key>/reports/Uxx_TAG.yyyy.mm.dd.eu4.zip (git LFS, see
.gitattributes) plus an entry in that folder's series.json with the save's quality and verification summary. Reports are
verified and logged but do not gate the calculation. The server never commits or pushes anything.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.trade import corpus
from app.trade.quality import SaveQuality
from app.trade.savefile import SaveText
from app.trade.verify import VerificationReport

_CASE_ID = re.compile(r"^U(\d+)$")


@dataclass(frozen=True)
class Store:
    root: Path            # datasets/eu4 (all datasets: case numbers are unique across them)
    series_dir: Path      # where this save goes

    @property
    def manifest_path(self) -> Path:
        return self.series_dir / "series.json"


@dataclass(frozen=True)
class StoredCase:
    id: str
    file: str
    duplicate: bool


def default_store(quality: SaveQuality) -> Store:
    root = Path(os.environ.get("EU4_DATASETS_DIR", corpus.DATASETS_DIR))
    return Store(root, corpus.dataset_dir(quality.game_version, quality.mods_key, quality.dlc_key, root) / "reports")


def flat_text(text: SaveText) -> str:
    """One loadable text document: meta first (player, date, version), then gamestate, unless they are the same text."""
    return text.gamestate if text.meta is text.gamestate or text.meta == text.gamestate else text.meta + "\n" + text.gamestate


def _read_series(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"series": "reports", "kind": corpus.REPORT_KIND,
            "description": "Saves users submitted from the app (expected to verify but did not). Not part of the CI bar until triaged.",
            "saves": []}


def next_case_number(store: Store) -> int:
    used = []
    for path in store.root.rglob("series.json") if store.root.exists() else []:
        for e in json.loads(path.read_text(encoding="utf-8"))["saves"]:
            m = _CASE_ID.match(e["id"])
            if m:
                used.append(int(m.group(1)))
    return max(used, default=0) + 1


def case_filename(number: int, tag: str, date: str) -> str:
    y, m, d = (date.split(".") + ["01", "01"])[:3] if date.count(".") >= 2 else (date, "01", "01")
    return f"U{number:02d}_{tag}.{int(y):04d}.{int(m):02d}.{int(d):02d}.eu4"


def store_case(text: SaveText, report: VerificationReport, quality: SaveQuality, store: Store | None = None) -> StoredCase:
    store = store or default_store(quality)
    body = flat_text(text)
    digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    series = _read_series(store.manifest_path)
    for e in series["saves"]:
        if e.get("sha256") == digest:
            return StoredCase(e["id"], e["file"], True)

    number = next_case_number(store)
    file = case_filename(number, report.player, report.date)
    store.series_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(store.series_dir / f"{file}.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(file, body)
    entry = {
        "id": f"U{number:02d}", "file": file, "tag": report.player, "date": report.date, "role": "report", "change": "",
        "covers": [], "sha256": digest, "quality": quality.to_dict(),
        "calc_version": report.calc_version, "status": report.status, "first_failing_stage": report.first_failing_stage,
    }
    series["saves"].append(entry)
    tmp = store.manifest_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(series, indent=2) + "\n", encoding="utf-8")
    tmp.replace(store.manifest_path)
    return StoredCase(entry["id"], file, False)
