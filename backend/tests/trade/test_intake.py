"""Intake of experiment saves: only clean saves that fit their series are accepted (app/trade/intake.py)."""
from __future__ import annotations

import json
import re

import pytest

from app.trade import corpus, intake


def _save(sid, tmp_path, rename=None):
    entry = next((e for e in corpus.manifest() if e["id"] == sid), None)
    path = corpus.locate(entry, tmp_path / sid) if entry else None
    if path is None:
        pytest.skip(f"dataset save {sid} not available (git lfs pull?)")
    return path


def test_series_a_then_b_and_the_rejections(tmp_path):
    root = tmp_path / "datasets"
    u27, u28, u04 = _save("U27", tmp_path), _save("U28", tmp_path), _save("U04", tmp_path)

    with pytest.raises(intake.Rejected, match="no A save"):
        intake.add_save(u28, "exp-test", "B1", "ragusa merchant sent", root=root)

    a = intake.add_save(u27, "exp-test", "A", "", description="test series", root=root)
    with pytest.raises(intake.Rejected, match="already has an A"):
        intake.add_save(u28, "exp-test", "A", "", root=root)
    with pytest.raises(intake.Rejected, match="control"):
        intake.add_save(u28, "exp-test", "C", "", root=root)                 # U28 moved a merchant: not a control
    with pytest.raises(intake.Rejected, match="same game"):
        intake.add_save(u04, "exp-test", "B1", "other game", root=root)

    b = intake.add_save(u28, "exp-test", "B1", "ragusa merchant sent (steer)", ["IV-03"], root=root)
    assert b.placements_changed == ["ragusa"]
    with pytest.raises(intake.Rejected, match="already in the series"):
        intake.add_save(u28, "exp-test", "B2", "again", root=root)

    entries = [e for e in corpus.manifest(root) if e["series"] == "exp-test"]
    assert [(e["id"], e["role"], e["kind"]) for e in entries] == [(a.id, "A", "experiment"), (b.id, "B1", "experiment")]
    assert entries[1]["base"] == a.id and entries[1]["covers"] == ["IV-03"] and entries[1]["quality"]["clean"]
    assert corpus.locate(entries[1], tmp_path / "back") is not None
    ds = json.loads((b.series_dir.parent / "dataset.json").read_text())
    assert ds["mods_key"] == "vanilla" and ds["dlcs"] == ["Art of War", "Common Sense", "Rights of Man"]


def test_mid_month_save_is_rejected(tmp_path):
    u27 = _save("U27", tmp_path)
    text = u27.read_text(encoding="utf-8", errors="replace")
    mid = tmp_path / "mid.eu4"
    mid.write_text(re.sub(r"(?m)^date=1445\.4\.1$", "date=1445.4.2", text, count=1), encoding="utf-8")
    with pytest.raises(intake.Rejected, match="mid_month"):
        intake.add_save(mid, "exp-test", "A", "", root=tmp_path / "datasets")
