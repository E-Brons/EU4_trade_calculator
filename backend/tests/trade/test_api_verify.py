"""POST /api/verify-save: the user is told, and a mismatching save is stored as a RED case (once)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.trade import corpus


@pytest.fixture()
def save_file(tmp_path):
    entry = next(e for e in corpus.manifest() if e["id"] == "S14")
    path = corpus.locate(entry, tmp_path / "s14")
    if path is None:
        pytest.skip("fixture S14 not available")
    return path


@pytest.fixture()
def store_env(tmp_path, monkeypatch):
    monkeypatch.setenv("EU4_CASE_ZIP_DIR", str(tmp_path / "zips"))
    monkeypatch.setenv("EU4_CASE_MANIFEST", str(tmp_path / "saves.json"))
    monkeypatch.delenv("EU4_STORE_CASES", raising=False)
    return tmp_path


def _post(client: TestClient, path: Path):
    with path.open("rb") as f:
        return client.post("/api/verify-save", files={"file": (path.name, f, "application/octet-stream")})


def test_mismatch_is_reported_and_stored_once(save_file, store_env):
    client = TestClient(app)
    r = _post(client, save_file)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["verification"]["status"] == "mismatch"          # RED while the calculation is incomplete
    assert body["verification"]["first_failing_stage"]
    assert body["stored_case"] == "U01"
    assert "does not reproduce" in body["message"] and "U01" in body["message"]
    manifest = json.loads((store_env / "saves.json").read_text(encoding="utf-8"))["saves"]
    assert [e["id"] for e in manifest] == ["U01"] and manifest[0]["expected"] == "red"
    assert (store_env / "zips" / f"{manifest[0]['file']}.zip").exists()

    again = _post(client, save_file).json()
    assert again["stored_case"] == "U01" and "already stored" in again["message"]
    assert len(list((store_env / "zips").glob("*.zip"))) == 1


def test_storing_can_be_disabled(save_file, store_env, monkeypatch):
    monkeypatch.setenv("EU4_STORE_CASES", "0")
    body = _post(TestClient(app), save_file).json()
    assert body["stored_case"] is None
    assert not (store_env / "zips").exists()


def test_not_a_save_is_rejected(store_env, tmp_path):
    junk = tmp_path / "junk.eu4"
    junk.write_text("not a save")
    r = _post(TestClient(app), junk)
    assert r.status_code == 422
