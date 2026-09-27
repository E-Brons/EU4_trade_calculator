import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.parsing import pdx_tools_melt

client = TestClient(app)

REAL_IRONMAN_SAVE = Path(
    "/Users/elkanabronstein/Documents/Paradox Interactive/Europa Universalis IV/save games/Ottomans_Ironman.eu4"
)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_get_tradenodes_has_80_nodes_and_known_ids():
    r = client.get("/api/tradenodes")
    assert r.status_code == 200
    data = r.json()
    assert len(data["nodes"]) == 80
    ids = {n["node_id"] for n in data["nodes"]}
    assert {"venice", "constantinople", "english_channel"} <= ids


def test_simulate_basic():
    body = {
        "node_states": {
            "venice": {
                "node_id": "venice",
                "local_value": 100.0,
                "is_home": True,
                "player_base_power": 10.0,
                "other_collect_power": 10.0,
            }
        },
        "allocation": {},
        "params": {},
    }
    r = client.post("/api/simulate", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["total_income"] == 50.0
    assert data["nodes"]["venice"]["display_name"] == "Venice"


def test_simulate_rejects_bad_shape():
    r = client.post("/api/simulate", json={"node_states": "not-a-dict"})
    assert r.status_code == 422


def test_optimize_end_to_end():
    body = {
        "node_states": {
            "constantinople": {
                "node_id": "constantinople",
                "local_value": 50.0,
                "player_base_power": 8.0,
            },
            "ragusa": {
                "node_id": "ragusa",
                "is_home": True,
                "player_base_power": 5.0,
            },
        },
        "params": {"merchant_power": 6.0},
        "home_node": "ragusa",
        "candidate_nodes": ["constantinople", "ragusa"],
        "max_merchants": 2,
        "max_light_ships": 0,
        "current_allocation": {},
    }
    r = client.post("/api/optimize", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["income"] > 0
    # current_allocation={} means no merchants anywhere; constantinople's
    # passive power still flows downstream into home (ragusa) automatically.
    assert data["current_income"] == 50.0
    assert data["income"] >= data["current_income"]
    assert isinstance(data["recommended_actions"], list)
    assert len(data["merchant_marginals"]) == 2
    assert len(data["ship_marginals"]) == 2


def test_optimize_rejects_unknown_node():
    body = {
        "node_states": {"not_a_real_node": {"node_id": "not_a_real_node"}},
        "home_node": "not_a_real_node",
        "max_merchants": 1,
        "max_light_ships": 0,
    }
    r = client.post("/api/optimize", json=body)
    assert r.status_code == 422


def test_import_save_end_to_end(tmp_path):
    gamestate = b"""EU4txt
player="TUR"
trade={
\tnode={
\t\tdefinitions="constantinople"
\t\tlocal_value=20.0
\t\ttotal=20.0
\t\tTUR={
\t\t\tprovince_power=9.0
\t\t\thas_capital=yes
\t\t}
\t}
}
"""
    save_path = tmp_path / "test.eu4"
    with zipfile.ZipFile(save_path, "w") as zf:
        zf.writestr("gamestate", gamestate)
        zf.writestr("meta", b'EU4txt\nplayer="TUR"\n')

    with open(save_path, "rb") as f:
        r = client.post("/api/import-save", files={"file": ("test.eu4", f, "application/octet-stream")})
    assert r.status_code == 200
    data = r.json()
    assert data["player_tag"] == "TUR"
    assert data["suggested_home_node"] == "constantinople"
    assert data["node_states"]["constantinople"]["player_base_power"] == 9.0


def test_root_serves_flutter_build_when_present():
    r = client.get("/")
    build_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "build" / "web"
    if not build_dir.exists():
        pytest.skip("frontend not built (run `flutter build web` in frontend/)")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "<html" in r.text.lower()


def test_import_save_rejects_non_zip(tmp_path):
    bogus = tmp_path / "bogus.eu4"
    bogus.write_bytes(b"not a zip file at all")
    with open(bogus, "rb") as f:
        r = client.post("/api/import-save", files={"file": ("bogus.eu4", f, "application/octet-stream")})
    assert r.status_code >= 400


def test_import_save_binary_ironman_gives_actionable_error_without_melt_worker(tmp_path, monkeypatch):
    # With no melt worker running and no rakaly CLI on PATH (the default
    # state of this sandbox), uploading a real binary Ironman save must
    # fail with a clear, actionable 422 -- never hang, never a bare 500.
    from app.parsing import rakaly

    monkeypatch.setattr(pdx_tools_melt, "available", lambda *a, **kw: False)
    monkeypatch.setattr(rakaly, "find_rakaly", lambda: None)

    save_path = tmp_path / "ironman.eu4"
    with zipfile.ZipFile(save_path, "w") as zf:
        zf.writestr("gamestate", b"EU4bin\x00fake binary payload")
        zf.writestr("meta", b"EU4bin\x00fake binary payload")

    with open(save_path, "rb") as f:
        r = client.post("/api/import-save", files={"file": ("ironman.eu4", f, "application/octet-stream")})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "pdx.tools" in detail
    assert "manually" in detail


@pytest.mark.skipif(
    not REAL_IRONMAN_SAVE.exists(),
    reason=f"real Ironman save fixture not present at {REAL_IRONMAN_SAVE}",
)
@pytest.mark.skipif(
    not pdx_tools_melt.available(),
    reason=(
        "no melt worker heartbeat detected -- this test exercises the live "
        "pdx.tools automation end-to-end and needs `python3 "
        "backend/tools/melt_worker.py` running in an unsandboxed terminal "
        "with real network access (blocked by design inside this sandbox)"
    ),
)
def test_import_save_real_ironman_end_to_end_via_live_melt_worker():
    """The actual success criterion for this feature: upload the real
    binary Ironman save and get back a fully parsed result with zero
    manual melting steps. Only runs when a melt worker is actually up."""
    with open(REAL_IRONMAN_SAVE, "rb") as f:
        r = client.post(
            "/api/import-save",
            files={"file": ("Ottomans_Ironman.eu4", f, "application/octet-stream")},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["player_tag"] == "TUR"
    assert len(data["node_states"]) >= 70  # ~80 trade nodes in a real save

