"""The submitted-save store: naming, numbering across datasets, de-duplication, and that a stored save loads back."""
from __future__ import annotations

import json
import zipfile

from app.trade import cases, corpus
from app.trade.quality import SaveQuality
from app.trade.savefile import SaveText
from app.trade.verify import ChainReport, VerificationReport

QUALITY = SaveQuality("tick_day", 0, 0, "1.37.5", True, "vanilla", "dlc-test")


def _report(player="TUR", date="1665.4.22") -> VerificationReport:
    return VerificationReport("upload", player, date, "test", "1.37.5", {}, ChainReport("fail"), {}, {})


def test_case_filename_pattern():
    assert cases.case_filename(1, "TUR", "1665.4.22") == "U01_TUR.1665.04.22.eu4"
    assert cases.case_filename(12, "VEN", "1444.11.11") == "U12_VEN.1444.11.11.eu4"


def test_store_numbering_dedupe_and_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("EU4_DATASETS_DIR", str(tmp_path))
    store = cases.default_store(QUALITY)
    assert store.series_dir == corpus.dataset_dir("1.37.5", "vanilla", "dlc-test", tmp_path) / "reports"
    text_a = SaveText(meta="EU4txt\nplayer=\"TUR\"\ndate=1665.4.22\n", gamestate="EU4txt\ntrade={}\n", ironman=False)
    text_b = SaveText(meta="EU4txt\nplayer=\"VEN\"\n", gamestate="EU4txt\nother\n", ironman=False)

    a = cases.store_case(text_a, _report("TUR", "1665.4.22"), QUALITY, store)
    assert (a.id, a.file, a.duplicate) == ("U01", "U01_TUR.1665.04.22.eu4", False)
    again = cases.store_case(text_a, _report("TUR", "1665.4.22"), QUALITY, store)
    assert (again.id, again.duplicate) == ("U01", True)
    assert len(list(store.series_dir.glob("*.zip"))) == 1
    b = cases.store_case(text_b, _report("VEN", "1444.11.11"), QUALITY, store)
    assert b.id == "U02"

    entries = corpus.manifest(tmp_path)
    assert [e["id"] for e in entries] == ["U01", "U02"]
    e = entries[0]
    assert (e["kind"], e["series"], e["tag"], e["date"]) == ("report", "reports", "TUR", "1665.4.22")
    assert len(e["sha256"]) == 64 and e["quality"]["clean"] is True
    assert corpus.selected(entries) == []                       # reports never gate the calculation
    path = corpus.locate(e, tmp_path / "out")
    assert path is not None and path.read_text(encoding="utf-8").startswith("EU4txt")
    with zipfile.ZipFile(e["zip"]) as zf:
        assert zf.namelist() == [e["file"]]
    json.loads(store.manifest_path.read_text(encoding="utf-8"))


def test_numbers_continue_after_existing_datasets(tmp_path):
    other = corpus.dataset_dir("1.37.5", "vanilla", "dlc-x", tmp_path) / "venice-1444"
    other.mkdir(parents=True)
    (other / "series.json").write_text(json.dumps({"series": "venice-1444", "saves": [{"id": "U29", "file": "f"}]}))
    store = cases.Store(tmp_path, corpus.dataset_dir("1.37.5", "vanilla", "dlc-y", tmp_path) / "reports")
    assert cases.next_case_number(store) == 30


def test_meta_and_gamestate_are_joined_when_they_differ():
    joined = cases.flat_text(SaveText(meta="META", gamestate="STATE", ironman=False))
    assert joined.startswith("META") and joined.endswith("STATE")
    same = "ALL"
    assert cases.flat_text(SaveText(meta=same, gamestate=same, ironman=False)) == "ALL"


def test_datasets_are_wellformed():
    """Every save of every series has a valid name, a real zip (git lfs pull must have run) and a matching hash."""
    import subprocess
    import sys
    from pathlib import Path
    backend = Path(__file__).resolve().parents[2]
    out = subprocess.run([sys.executable, "scripts/check_datasets.py"], cwd=backend, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
