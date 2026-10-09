"""Sanity checks on the committed map asset (frontend/assets/map/world_map.json)."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
ASSET = ROOT / "frontend" / "assets" / "map" / "world_map.json"
GRAPH = ROOT / "backend" / "data" / "tradenodes.json"

pytestmark = pytest.mark.skipif(not ASSET.exists(), reason="map asset not generated")


@pytest.fixture(scope="module")
def data():
    return json.loads(ASSET.read_text())


@pytest.fixture(scope="module")
def graph():
    return json.loads(GRAPH.read_text())


def test_all_nodes_and_routes_present(data, graph):
    assert set(data["nodes"]) == set(graph["nodes"])
    edges = {(n, o["target"]) for n, v in graph["nodes"].items() for o in v["outgoing"]}
    assert {(r["from"], r["to"]) for r in data["routes"]} == edges
    assert len(data["routes"]) == len(edges)


def test_rings_and_coordinates(data):
    w, h = data["width"], data["height"]

    def check(ring):
        assert len(ring) % 2 == 0 and len(ring) >= 6
        assert all(0 <= x <= w for x in ring[0::2])
        assert all(0 <= y <= h for y in ring[1::2])

    for ring in data["land"]:
        check(ring)
    for node in data["nodes"].values():
        assert node["rings"]
        for ring in node["rings"]:
            check(ring)


def test_anchor_near_bbox(data):
    # anchors may sit at sea (the game's `location` province), so only require nearness
    for nid, n in data["nodes"].items():
        x0, y0, x1, y1 = n["bbox"]
        ax, ay = n["anchor"]
        assert x0 - 400 <= ax <= x1 + 400 and y0 - 400 <= ay <= y1 + 400, nid
        assert n["area"] > 0 and 0 <= n["land_fraction"] <= 1


def _shoelace(flat):
    xs, ys = flat[0::2], flat[1::2]
    return 0.5 * sum(xs[i] * ys[(i + 1) % len(xs)] - xs[(i + 1) % len(xs)] * ys[i] for i in range(len(xs)))


def _even_odd_area(rings):
    """Net area: the tracer orients outer rings and holes oppositely, so the signed sum is the filled area."""
    return abs(sum(_shoelace(r) for r in rings))


def test_regions_are_land_only(data, graph):
    fallback = set(data["water_only_nodes"])
    # only nodes with no land member may be water-only
    import re

    default_map = Path.home() / "Library/Application Support/Steam/steamapps/common/Europa Universalis IV/map/default.map"
    if default_map.exists():
        text = default_map.read_text(encoding="latin-1")
        water = set()
        for key in ("sea_starts", "lakes"):
            m = re.search(rf"\b{key}\s*=\s*\{{([^}}]*)\}}", text)
            water |= {int(x) for x in re.findall(r"\d+", m.group(1))}
        expected = {nid for nid, n in graph["nodes"].items() if all(p in water for p in n["member_provinces"])}
        assert fallback == expected
    for nid, n in data["nodes"].items():
        assert n["land_fraction"] == (0.0 if nid in fallback else 1.0), nid
    # the union of all land-only node regions can never exceed the land area
    land = _even_odd_area(data["land"])
    regions = sum(_even_odd_area(n["rings"]) for nid, n in data["nodes"].items() if nid not in fallback)
    assert regions <= land * 1.01
    # and every region's pixel area is bounded by its rings' bbox
    for nid, n in data["nodes"].items():
        x0, y0, x1, y1 = n["bbox"]
        assert n["area"] <= (x1 - x0 + 1) * (y1 - y0 + 1), nid


def test_region_vertices_lie_on_land_coast(data):
    """Region outlines are built from the same arcs as `land`: every vertex of a
    land-only node ring is also a vertex of some land ring."""
    land_pts = {(r[i], r[i + 1]) for r in data["land"] for i in range(0, len(r), 2)}
    fallback = set(data["water_only_nodes"])
    total = shared = 0
    for nid, n in data["nodes"].items():
        if nid in fallback:
            continue
        for r in n["rings"]:
            for i in range(0, len(r), 2):
                total += 1
                shared += (r[i], r[i + 1]) in land_pts
    # inland borders between regions are not coast, but a large share of vertices are
    assert shared / total > 0.3


def test_routes_run_from_source_anchor_to_target_anchor(data):
    w, h = data["width"], data["height"]
    for r in data["routes"]:
        p = r["points"]
        assert len(p) >= 6 and len(p) % 2 == 0, (r["from"], r["to"])
        assert all(-w <= x <= 2 * w for x in p[0::2]) and all(0 <= y <= h for y in p[1::2])
        assert p[0:2] == data["nodes"][r["from"]]["anchor"]
        ax, ay = data["nodes"][r["to"]]["anchor"]
        assert (p[-2] - ax) % w == 0 and p[-1] == ay  # equal modulo the Pacific wrap
        # unwrapped: consecutive points never jump half the map
        assert all(abs(p[i + 2] - p[i]) < w / 2 for i in range(0, len(p) - 2, 2))


def test_control_points_are_plausible_bends(data):
    """Bend points sit between/near their two nodes (catches flipped y or reversed order)."""
    for r in data["routes"]:
        p = r["points"]
        ctrl = list(zip(p[2:-2:2], p[3:-2:2]))
        (ax, ay), (bx, by) = data["nodes"][r["from"]]["anchor"], data["nodes"][r["to"]]["anchor"]
        if abs(bx - ax) > 2000:  # Pacific seam routes
            continue
        span = max(abs(bx - ax), abs(by - ay), 100)
        for x, y in ctrl:
            assert min(ax, bx) - span <= x <= max(ax, bx) + span, (r["from"], r["to"])
            assert min(ay, by) - span <= y <= max(ay, by) + span, (r["from"], r["to"])
