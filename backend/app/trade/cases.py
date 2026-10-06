"""Stores uploaded saves whose calculation does not verify, as new fixtures (RED), for later investigation.

A case is the flat save text zipped as backend/tests/fixtures/saves_zip/Uxx_TAG.yyyy.mm.dd.eu4.zip (tracked with git LFS, see
.gitattributes) plus a manifest entry in tests/fixtures/saves/saves.json with kind "user_case" and expected "red".
When calc.py is fixed the strict-xfail test for that case flips; changing `expected` to "green" turns it into a regression test.
The server never commits or pushes anything.
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
from app.trade.savefile import SaveText
from app.trade.verify import VerificationReport

_CASE_ID = re.compile(r"^U(\d+)$")


@dataclass(frozen=True)
class Store:
    zip_dir: Path
    manifest_path: Path


@dataclass(frozen=True)
class StoredCase:
    id: str
    file: str
    duplicate: bool


def default_store() -> Store:
    return Store(
        zip_dir=Path(os.environ.get("EU4_CASE_ZIP_DIR", corpus.ZIP_DIR)),
        manifest_path=Path(os.environ.get("EU4_CASE_MANIFEST", corpus.MANIFEST_PATH)),
    )


def flat_text(text: SaveText) -> str:
    """One loadable text document: meta first (player, date, version), then gamestate, unless they are the same text."""
    return text.gamestate if text.meta is text.gamestate or text.meta == text.gamestate else text.meta + "\n" + text.gamestate


def _read_manifest(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"saves": []}


def next_case_number(store: Store) -> int:
    used = []
    for e in _read_manifest(store.manifest_path)["saves"]:
        m = _CASE_ID.match(e["id"])
        if m:
            used.append(int(m.group(1)))
    for p in store.zip_dir.glob("U*_*.eu4.zip") if store.zip_dir.exists() else []:
        m = re.match(r"^U(\d+)_", p.name)
        if m:
            used.append(int(m.group(1)))
    return max(used, default=0) + 1


def case_filename(number: int, tag: str, date: str) -> str:
    y, m, d = (date.split(".") + ["01", "01"])[:3] if date.count(".") >= 2 else (date, "01", "01")
    return f"U{number:02d}_{tag}.{int(y):04d}.{int(m):02d}.{int(d):02d}.eu4"


def store_case(text: SaveText, report: VerificationReport, store: Store | None = None) -> StoredCase:
    store = store or default_store()
    body = flat_text(text)
    digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    manifest = _read_manifest(store.manifest_path)
    for e in manifest["saves"]:
        if e.get("sha256") == digest:
            return StoredCase(e["id"], e["file"], True)

    number = next_case_number(store)
    file = case_filename(number, report.player, report.date)
    store.zip_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(store.zip_dir / f"{file}.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(file, body)
    entry = {
        "id": f"U{number:02d}", "file": file, "tag": report.player, "date": report.date, "kind": "user_case", "expected": "red",
        "sha256": digest, "calc_version": report.calc_version, "first_failing_stage": report.first_failing_stage,
    }
    manifest["saves"].append(entry)
    tmp = store.manifest_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    tmp.replace(store.manifest_path)
    return StoredCase(entry["id"], file, False)
