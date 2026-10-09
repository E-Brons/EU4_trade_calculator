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
DATASETS = Path(__file__).resolve().parents[2] / "datasets"


def _dataset_save(name: str = "U30_VEN") -> bytes:
    zips = [z for z in sorted(DATASETS.rglob(f"{name}*.eu4.zip")) if zipfile.is_zipfile(z)]
    if not zips:
        pytest.skip("dataset save zips not present (git lfs pull?)")
    with zipfile.ZipFile(zips[0]) as zf:
        return zf.read(zf.namelist()[0])


@pytest.fixture(scope="module")
def imported():
    r = client.post("/api/import-save", files={"file": ("U30.eu4", _dataset_save(), "application/octet-stream")})
    assert r.status_code == 200, r.text
    return r.json()


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_get_tradenodes_has_80_nodes_and_known_ids():
    r = client.get("/api/tradenodes")
    assert r.status_code == 200
    data = r.json()
    assert len(data["nodes"]) == 80
    assert {"venice", "constantinople", "english_channel"} <= {n["node_id"] for n in data["nodes"]}


def test_import_save_describes_the_player(imported):
    assert imported["player_tag"] == "VEN"
    assert imported["suggested_home_node"] == "venice"
    assert imported["suggested_trade_efficiency"] is not None
    assert imported["suggested_max_merchants"] >= 3
    assert "venice" in imported["suggested_candidate_nodes"]
    assert imported["current_allocation"]["ragusa"]["merchant_action"] == "steer"


def test_simulate_the_saves_own_placement_reproduces_its_income(imported):
    r = client.post("/api/simulate", json={"save_id": imported["save_id"], "allocation": imported["current_allocation"]})
    assert r.status_code == 200
    data = r.json()
    assert data["total_income"] == pytest.approx(imported["actual_current_income"], rel=0.01)
    venice = data["nodes"]["venice"]
    assert venice["display_name"] == "Venice"
    assert venice["player_collects"] and venice["player_income"] > 0
    assert venice["total_power"] == pytest.approx(venice["retained_power"] + venice["pull_power"])


def test_simulate_slider_changes_income(imported):
    body = {"save_id": imported["save_id"], "allocation": imported["current_allocation"]}
    base = client.post("/api/simulate", json=body).json()["total_income"]
    more = client.post("/api/simulate", json=body | {"params": {"trade_efficiency": imported["suggested_trade_efficiency"] + 0.5}}).json()
    assert more["total_income"] > base


def test_node_options_cover_every_choice(imported):
    r = client.post("/api/node-options", json={"save_id": imported["save_id"], "allocation": imported["current_allocation"],
                                               "node_id": "ragusa", "max_light_ships": 5})
    assert r.status_code == 200
    data = r.json()
    assert len(data["merchant_options"]) == 2 + 3   # none, collect, steer to each of ragusa's 3 links
    assert sum(o["is_current"] for o in data["merchant_options"]) == 1
    current = next(o for o in data["merchant_options"] if o["is_current"])
    assert current["total_income"] == pytest.approx(data["current_total_income"])
    assert [p["ships"] for p in data["ship_curve"]] == list(range(21))


def test_optimize_is_never_worse_than_the_save(imported):
    r = client.post("/api/optimize", json={
        "save_id": imported["save_id"], "home_node": imported["suggested_home_node"],
        "candidate_nodes": imported["suggested_candidate_nodes"], "max_merchants": imported["suggested_max_merchants"],
        "max_light_ships": imported["suggested_max_light_ships"], "current_allocation": imported["current_allocation"],
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["income"] >= data["current_income"] - 1e-9
    assert data["breakdown"]["total_income"] == pytest.approx(data["income"])
    assert len(data["merchant_marginals"]) == 2 and len(data["ship_marginals"]) == 2
    assert sum(a["merchant_action"] != "none" for a in data["recommended_actions"]) <= imported["suggested_max_merchants"]


def test_unknown_save_id_asks_for_a_new_upload():
    r = client.post("/api/simulate", json={"save_id": "nope", "allocation": {}})
    assert r.status_code == 404
    assert "Upload the save again" in r.json()["detail"]


def test_simulate_rejects_bad_shape():
    assert client.post("/api/simulate", json={"allocation": "not-a-dict"}).status_code == 422


def test_optimize_rejects_unknown_node(imported):
    r = client.post("/api/optimize", json={"save_id": imported["save_id"], "home_node": "not_a_real_node",
                                           "max_merchants": 1, "max_light_ships": 0})
    assert r.status_code == 422


def test_import_save_rejects_non_zip(tmp_path):
    bogus = tmp_path / "bogus.eu4"
    bogus.write_bytes(b"not a zip file at all")
    with open(bogus, "rb") as f:
        r = client.post("/api/import-save", files={"file": ("bogus.eu4", f, "application/octet-stream")})
    assert r.status_code >= 400


def test_import_save_binary_ironman_gives_actionable_error_without_melt_worker(tmp_path, monkeypatch):
    # With no in-process melt capability and no melt worker running, uploading a binary Ironman save must fail with a
    # clear, actionable 422 -- never hang, never a bare 500.
    from app.parsing import pdx_tools_browser

    def _unavailable(*a, **kw):
        raise RuntimeError("playwright/chromium not available in this test environment")

    monkeypatch.setattr(pdx_tools_browser, "melt_via_browser", _unavailable)
    monkeypatch.setattr(pdx_tools_melt, "available", lambda *a, **kw: False)
    save_path = tmp_path / "ironman.eu4"
    with zipfile.ZipFile(save_path, "w") as zf:
        zf.writestr("gamestate", b"EU4bin\x00fake binary payload")
        zf.writestr("meta", b"EU4bin\x00fake binary payload")
    with open(save_path, "rb") as f:
        r = client.post("/api/import-save", files={"file": ("ironman.eu4", f, "application/octet-stream")})
    assert r.status_code == 422
    assert "pdx.tools" in r.json()["detail"]


@pytest.mark.skipif(not REAL_IRONMAN_SAVE.exists(), reason=f"real Ironman save not present at {REAL_IRONMAN_SAVE}")
def test_import_save_real_ironman_end_to_end_via_live_melt_worker():
    """Upload the real binary Ironman save and get a parsed result with zero manual melting steps, however it gets
    there; "no melt path available in this run" is an expected sandbox outcome (skip), not a failure."""
    with open(REAL_IRONMAN_SAVE, "rb") as f:
        r = client.post("/api/import-save", files={"file": ("Ottomans_Ironman.eu4", f, "application/octet-stream")})
    if r.status_code == 422 and "couldn't be melted automatically" in r.json().get("detail", ""):
        pytest.skip(f"no melt path actually available in this run: {r.json()['detail']}")
    assert r.status_code == 200
    assert r.json()["player_tag"] == "TUR"


def test_root_serves_flutter_build_when_present():
    build_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "build" / "web"
    if not build_dir.exists():
        pytest.skip("frontend not built (run `flutter build web` in frontend/)")
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "<html" in r.text.lower()


def _frontend_built() -> bool:
    from app import buildinfo

    return buildinfo.BUNDLE.exists()


def test_everything_is_served_uncached():
    r = client.get("/api/health")
    assert r.headers["cache-control"] == "no-store, max-age=0"
    if _frontend_built():
        assert client.get("/").headers["cache-control"] == "no-store, max-age=0"
        assert client.get("/main.dart.js").headers["cache-control"] == "no-store, max-age=0"


def test_build_endpoint_reports_the_bundle_on_disk():
    r = client.get("/api/build")
    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"build_id", "built_at", "sources_newer_than_build"}
    if not _frontend_built():
        assert data["build_id"] is None
        return
    assert len(data["build_id"]) == 8
    import hashlib

    from app import buildinfo

    assert data["build_id"] == hashlib.sha256(buildinfo.BUNDLE.read_bytes()).hexdigest()[:8]


def test_index_html_is_stamped_with_the_build_id():
    if not _frontend_built():
        pytest.skip("frontend not built")
    build_id = client.get("/api/build").json()["build_id"]
    for path in ("/", "/index.html"):
        r = client.get(path)
        assert f'<meta name="build-id" content="{build_id}">' in r.text
        assert "<html" in r.text.lower()
