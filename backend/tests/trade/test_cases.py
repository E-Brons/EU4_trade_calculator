"""The mismatch case store: naming, numbering, de-duplication, and that a stored case loads back as a fixture."""
from __future__ import annotations

import json
import zipfile

from app.trade import cases, corpus
from app.trade.savefile import SaveText
from app.trade.verify import ChainReport, VerificationReport


def _report(player="TUR", date="1665.4.22") -> VerificationReport:
    return VerificationReport("upload", player, date, "test", "1.37.5", {}, ChainReport("fail"), {}, {})


def test_case_filename_pattern():
    assert cases.case_filename(1, "TUR", "1665.4.22") == "U01_TUR.1665.04.22.eu4"
    assert cases.case_filename(12, "VEN", "1444.11.11") == "U12_VEN.1444.11.11.eu4"


def test_store_numbering_dedupe_and_reload(tmp_path):
    store = cases.Store(tmp_path / "zips", tmp_path / "saves.json")
    text_a = SaveText(meta="EU4txt\nplayer=\"TUR\"\ndate=1665.4.22\n", gamestate="EU4txt\ntrade={}\n", ironman=False)
    text_b = SaveText(meta="EU4txt\nplayer=\"VEN\"\n", gamestate="EU4txt\nother\n", ironman=False)

    a = cases.store_case(text_a, _report("TUR", "1665.4.22"), store)
    assert (a.id, a.file, a.duplicate) == ("U01", "U01_TUR.1665.04.22.eu4", False)
    assert (store.zip_dir / "U01_TUR.1665.04.22.eu4.zip").exists()

    again = cases.store_case(text_a, _report("TUR", "1665.4.22"), store)
    assert (again.id, again.duplicate) == ("U01", True)
    assert len(list(store.zip_dir.glob("*.zip"))) == 1

    b = cases.store_case(text_b, _report("VEN", "1444.11.11"), store)
    assert b.id == "U02"

    entries = corpus.manifest(store.manifest_path)
    assert [e["id"] for e in entries] == ["U01", "U02"]
    e = entries[0]
    assert (e["kind"], e["expected"], e["tag"], e["date"]) == ("user_case", "red", "TUR", "1665.4.22")
    assert len(e["sha256"]) == 64

    path = corpus.locate(e, tmp_path / "out", zip_dir=store.zip_dir, saves_dir=tmp_path / "nowhere")
    assert path is not None and path.read_text(encoding="utf-8").startswith("EU4txt")
    with zipfile.ZipFile(store.zip_dir / f"{e['file']}.zip") as zf:
        assert zf.namelist() == [e["file"]]
    json.loads(store.manifest_path.read_text(encoding="utf-8"))


def test_meta_and_gamestate_are_joined_when_they_differ():
    joined = cases.flat_text(SaveText(meta="META", gamestate="STATE", ironman=False))
    assert joined.startswith("META") and joined.endswith("STATE")
    same = "ALL"
    assert cases.flat_text(SaveText(meta=same, gamestate=same, ironman=False)) == "ALL"


def test_stored_user_cases_are_wellformed():
    """Every stored case in the real manifest has a valid name, a zip, and a matching hash (git lfs pull must have run)."""
    import subprocess
    import sys
    from pathlib import Path
    entries = [e for e in corpus.manifest() if e["kind"] == "user_case"]
    if not entries:
        return
    backend = Path(__file__).resolve().parents[2]
    out = subprocess.run([sys.executable, "scripts/promote_case.py", "--check"], cwd=backend, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
