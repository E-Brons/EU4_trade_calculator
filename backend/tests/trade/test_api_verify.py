"""POST /api/verify-save: the user is told how the save compares and how fair a test it is; it is stored only on request."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.trade import corpus


@pytest.fixture()
def save_file(tmp_path):
    entry = next((e for e in corpus.manifest() if e["id"] == "U27"), None)
    path = corpus.locate(entry, tmp_path / "u27") if entry else None
    if path is None:
        pytest.skip("dataset save U27 not available (git lfs pull?)")
    return path


@pytest.fixture()
def store_env(tmp_path, monkeypatch):
    monkeypatch.setenv("EU4_DATASETS_DIR", str(tmp_path / "datasets"))
    return tmp_path / "datasets"


def _post(client: TestClient, path: Path, store: bool = False):
    with path.open("rb") as f:
        return client.post("/api/verify-save", files={"file": (path.name, f, "application/octet-stream")},
                           data={"store": "true" if store else "false"})


def test_report_and_quality_without_storing(save_file, store_env):
    body = _post(TestClient(app), save_file).json()
    assert body["verification"]["status"] in ("verified", "mismatch")
    assert body["quality"]["timing"] == "tick_day" and body["quality"]["clean"] is True
    assert body["stored_case"] is None
    assert not store_env.exists()


def test_store_on_request_once(save_file, store_env):
    client = TestClient(app)
    body = _post(client, save_file, store=True).json()
    assert body["stored_case"] == "U01"
    series = list(store_env.rglob("series.json"))
    assert len(series) == 1 and series[0].parent.name == "reports"
    saves = json.loads(series[0].read_text(encoding="utf-8"))["saves"]
    assert [e["id"] for e in saves] == ["U01"] and saves[0]["quality"]["clean"] is True
    again = _post(client, save_file, store=True).json()
    assert again["stored_case"] == "U01" and "already stored" in again["message"]
    assert len(list(series[0].parent.glob("*.zip"))) == 1


def test_not_a_save_is_rejected(store_env, tmp_path):
    junk = tmp_path / "junk.eu4"
    junk.write_text("not a save")
    r = _post(TestClient(app), junk)
    assert r.status_code == 422
