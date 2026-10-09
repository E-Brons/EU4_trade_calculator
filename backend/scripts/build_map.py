"""Build frontend/assets/map/world_map.json from the EU4 game files.

Usage (system python3 with numpy + Pillow; NOT needed at runtime):
    python3 backend/scripts/build_map.py [path-to-eu4-install] [--preview]

Reads map/provinces.bmp, map/definition.csv, map/default.map,
map/positions.txt and common/tradenodes/00_tradenodes.txt and writes a
self-contained vector asset (no game textures) with, in map pixel space
(5632x2048, y pointing DOWN):

  land   coastline rings of every non-sea, non-lake province (even-odd fill)
  nodes  per trade node: anchor (the `location` province, may be at sea), bbox,
         pixel area, land_fraction and the outline rings of the union of its
         LAND member provinces (even-odd fill); sea_starts/lakes are excluded.
         A node with no land member would keep its water members (listed in
         `water_only_nodes`; currently none). Node and `land` rings share the
         same simplified boundary arcs, so coastlines are identical.
  routes one per graph edge: from-anchor, the game's `control` bend points
         (y flipped), to-anchor. Meant as a Catmull-Rom/smooth spline through
         the points. x is unwrapped for routes crossing the Pacific seam, so it
         may leave [0, width] (draw a copy shifted by +-width).

Region boundaries are traced along exact pixel edges. Each boundary arc
shared by two regions is simplified ONCE (Douglas-Peucker, TOLERANCE px) and
reused by both neighbours, so adjacent regions still meet exactly. No
smoothing is applied; the client may smooth.

EU4 positions.txt / tradenodes control points measure y from the BOTTOM of
the map; they are flipped here with `height - y`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.parsing.clausewitz import as_list, parse  # noqa: E402

OUT = ROOT / "frontend" / "assets" / "map" / "world_map.json"
TRADENODES_JSON = ROOT / "backend" / "data" / "tradenodes.json"
TOLERANCE = 1.25
MIN_RING_AREA = 2.0  # px^2; drops specks that simplification collapsed

INSTALL_CANDIDATES = [
    "~/Library/Application Support/Steam/steamapps/common/Europa Universalis IV",
    "~/.steam/steam/steamapps/common/Europa Universalis IV",
    "C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV",
]


def find_install(arg: str | None) -> Path:
    cands = [arg] if arg else INSTALL_CANDIDATES
    for c in cands:
        p = Path(c).expanduser()
        if (p / "map" / "provinces.bmp").exists():
            return p
    raise SystemExit("Could not find an EU4 install. Pass the install directory as an argument.")


# --------------------------------------------------------------------- inputs

def load_province_image(install: Path) -> np.ndarray:
    """(H, W) int32 province id per pixel, row 0 = top of the picture."""
    rgb = np.asarray(Image.open(install / "map" / "provinces.bmp").convert("RGB"), dtype=np.int64)
    keys = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
    ids, kk = [], []
    for line in (install / "map" / "definition.csv").read_text(encoding="latin-1").splitlines()[1:]:
        parts = line.split(";")
        if len(parts) < 4 or not parts[0].strip().isdigit():
            continue
        pid = int(parts[0])
        if pid == 0:
            continue
        ids.append(pid)
        kk.append((int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3]))
    ids_a, kk_a = np.array(ids, dtype=np.int32), np.array(kk, dtype=np.int64)
    order = np.argsort(kk_a)
    kk_a, ids_a = kk_a[order], ids_a[order]
    pos = np.clip(np.searchsorted(kk_a, keys), 0, len(kk_a) - 1)
    return np.where(kk_a[pos] == keys, ids_a[pos], 0).astype(np.int32)


def parse_id_list(text: str, key: str) -> set[int]:
    m = re.search(rf"\b{key}\s*=\s*\{{([^}}]*)\}}", text)
    return {int(x) for x in re.findall(r"\d+", m.group(1))} if m else set()


def load_positions(install: Path, height: int) -> dict[int, tuple[float, float]]:
    """Province id -> city position in y-down map pixels."""
    text = (install / "map" / "positions.txt").read_text(encoding="latin-1")
    out = {}
    for m in re.finditer(r"^(\d+)=\{\s*position=\{([^}]*)\}", text, re.M):
        nums = [float(x) for x in m.group(2).split()]
        out[int(m.group(1))] = (nums[0], height - nums[1])
    return out


# --------------------------------------------------------------------- tracing

def _dp(pts: np.ndarray, tol: float) -> np.ndarray:
    """Douglas-Peucker on an open polyline; returns indices to keep."""
    n = len(pts)
    keep = np.zeros(n, dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        seg = pts[a + 1:b]
        p, q = pts[a], pts[b]
        d = q - p
        norm = float(np.hypot(*d))
        if norm == 0:
            dist = np.hypot(seg[:, 0] - p[0], seg[:, 1] - p[1])
        else:
            dist = np.abs(d[0] * (seg[:, 1] - p[1]) - d[1] * (seg[:, 0] - p[0])) / norm
        i = int(np.argmax(dist))
        if dist[i] > tol:
            m = a + 1 + i
            keep[m] = True
            stack.append((a, m))
            stack.append((m, b))
    return np.nonzero(keep)[0]


def _simplify_arc(pts: np.ndarray, tol: float) -> np.ndarray:
    if len(pts) <= 2:
        return pts
    closed = bool((pts[0] == pts[-1]).all())
    if closed:
        # split a closed loop at the point farthest from its start
        far = int(np.argmax(np.hypot(*(pts - pts[0]).T)))
        a = pts[: far + 1][_dp(pts[: far + 1], tol)]
        b = pts[far:][_dp(pts[far:], tol)]
        return np.vstack([a, b[1:]])
    return pts[_dp(pts, tol)]


def trace_arcs(label: np.ndarray, tol: float):
    """Crack-edge trace the label image into boundary arcs between junction
    vertices: list of (start_vertex, end_vertex, simplified (N,2) pts, left, right)."""
    H, W = label.shape
    P = np.pad(label, 1)
    # horizontal crack edges: (x,y)->(x+1,y), between rows y-1 and y
    above, below = P[0:H + 1, 1:W + 1], P[1:H + 2, 1:W + 1]
    hy, hx = np.nonzero(above != below)
    h_left, h_right = above[hy, hx], below[hy, hx]
    # vertical crack edges: (x,y)->(x,y+1), between columns x-1 and x
    lp, rp = P[1:H + 1, 0:W + 1], P[1:H + 1, 1:W + 2]
    vy, vx = np.nonzero(lp != rp)
    v_left, v_right = rp[vy, vx], lp[vy, vx]

    stride = W + 1
    u = np.concatenate([hy * stride + hx, vy * stride + vx])
    v = np.concatenate([hy * stride + hx + 1, (vy + 1) * stride + vx])
    eleft = np.concatenate([h_left, v_left]).tolist()
    eright = np.concatenate([h_right, v_right]).tolist()
    n = len(u)

    uniq, inv = np.unique(np.concatenate([u, v]), return_inverse=True)
    cu, cv = inv[:n], inv[n:]
    K = len(uniq)
    vxs, vys = (uniq % stride).astype(np.int32), (uniq // stride).astype(np.int32)
    deg = np.bincount(inv, minlength=K)
    ends = np.concatenate([cu, cv])
    order = np.argsort(ends, kind="stable")
    starts = np.concatenate([[0], np.cumsum(deg)])
    inc_edges = (np.concatenate([np.arange(n), np.arange(n)])[order]).tolist()
    starts_l, deg_l = starts.tolist(), deg.tolist()
    cu_l, cv_l = cu.tolist(), cv.tolist()

    visited = bytearray(n)
    arcs: list[tuple[list[int], int, int]] = []  # (vertices, left, right)

    def walk(s: int, e: int) -> None:
        verts = [s]
        left = eleft[e] if cu_l[e] == s else eright[e]
        right = eright[e] if cu_l[e] == s else eleft[e]
        cur = s
        while True:
            visited[e] = 1
            nxt = cv_l[e] if cu_l[e] == cur else cu_l[e]
            verts.append(nxt)
            if deg_l[nxt] != 2 or nxt == s:
                break
            a, b = inc_edges[starts_l[nxt]], inc_edges[starts_l[nxt] + 1]
            e = b if a == e else a
            cur = nxt
        arcs.append((verts, left, right))

    for s in np.nonzero(deg != 2)[0].tolist():
        for k in range(starts_l[s], starts_l[s + 1]):
            e = inc_edges[k]
            if not visited[e]:
                walk(s, e)
    for e in range(n):  # pure loops with no junction
        if not visited[e]:
            walk(cu_l[e], e)

    # simplify every arc exactly once; both neighbours reuse the same points
    out_arcs = []
    for verts, left, right in arcs:
        idx = np.asarray(verts)
        pts = np.stack([vxs[idx], vys[idx]], axis=1).astype(np.float64)
        out_arcs.append((verts[0], verts[-1], _simplify_arc(pts, tol).astype(np.int32), left, right))
    return out_arcs


def assemble_rings(arcs, is_in) -> list[np.ndarray]:
    """Rings of the region {pixels whose label satisfies is_in}: every arc with
    exactly one side inside is oriented inside-on-left and chained into loops."""
    by_start: dict[int, list[tuple[int, np.ndarray]]] = {}
    for a, b, pts, left, right in arcs:
        li, ri = is_in(left), is_in(right)
        if li and not ri:
            by_start.setdefault(a, []).append((b, pts))
        elif ri and not li:
            by_start.setdefault(b, []).append((a, pts[::-1]))
    out = []
    while by_start:
        s0 = next(iter(by_start))
        cur = s0
        pieces = []
        while True:
            lst = by_start.get(cur)
            if not lst:
                break  # unbalanced (should not happen)
            nxt, pts = lst.pop()
            if not lst:
                del by_start[cur]
            pieces.append(pts[:-1])
            cur = nxt
            if cur == s0:
                break
        if pieces:
            ring = np.vstack(pieces)
            if len(ring) >= 3 and abs(_area(ring)) >= MIN_RING_AREA:
                out.append(ring)
    return out


def _area(r: np.ndarray) -> float:
    x, y = r[:, 0].astype(np.float64), r[:, 1].astype(np.float64)
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _flat(r: np.ndarray) -> list[int]:
    return r.reshape(-1).astype(int).tolist()


# -------------------------------------------------------------------------- main

def build(install: Path) -> dict:
    prov = load_province_image(install)
    H, W = prov.shape
    default_map = (install / "map" / "default.map").read_text(encoding="latin-1")
    water = parse_id_list(default_map, "sea_starts") | parse_id_list(default_map, "lakes")
    positions = load_positions(install, H)

    tree = parse((install / "common" / "tradenodes" / "00_tradenodes.txt").read_text(encoding="utf-8-sig"))
    node_ids = sorted(tree)
    node_index = {nid: i + 1 for i, nid in enumerate(node_ids)}
    land_other = len(node_ids) + 1  # land provinces that belong to no node
    maxp = int(prov.max()) + 1

    # Node regions cover LAND members only; a node with no land member keeps
    # its water members so it still appears on the map.
    water_only = []
    prov_label = np.full(maxp + 1, 0, dtype=np.int32)
    prov_label[1:] = land_other
    for p in water:
        if p <= maxp:
            prov_label[p] = 0
    for nid, body in tree.items():
        members = as_list(body.get("members"))
        land_members = [p for p in members if p not in water]
        if not land_members:
            water_only.append(nid)
            land_members = members
        for p in land_members:
            prov_label[p] = node_index[nid]
    prov_label[0] = 0
    land_labels = {node_index[n] for n in node_ids if n not in water_only} | {land_other}
    is_land_lab = np.zeros(land_other + 1, dtype=bool)
    is_land_lab[list(land_labels)] = True

    label = prov_label[prov]

    print("tracing...", flush=True)
    arcs = trace_arcs(label, TOLERANCE)
    # `land` and node regions come from the SAME simplified arcs, so a
    # node's coastline is identical to the land coastline.
    land_rings = assemble_rings(arcs, lambda l: bool(is_land_lab[l]))
    node_rings = {node_index[n]: assemble_rings(arcs, (lambda i: lambda l: l == i)(node_index[n])) for n in node_ids}

    areas = np.bincount(label.ravel(), minlength=land_other + 1)

    nodes = {}
    for nid in node_ids:
        i = node_index[nid]
        rings = node_rings.get(i, [])
        if not rings:
            raise SystemExit(f"node {nid} produced no rings")
        allp = np.vstack(rings)
        bbox = [int(allp[:, 0].min()), int(allp[:, 1].min()), int(allp[:, 0].max()), int(allp[:, 1].max())]
        loc = tree[nid].get("location")
        ax, ay = positions.get(loc, (0, 0))
        ax, ay = int(round(ax)), int(round(ay))
        # anchor stays at the game's `location` province even if that is at sea
        inside = 0 <= ax < W and 0 <= ay < H and label[ay, ax] == i
        nodes[nid] = {
            "anchor": [ax, ay],
            "anchor_from_location": bool(inside),
            "bbox": bbox,
            "area": int(areas[i]),
            "land_fraction": 0.0 if nid in water_only else 1.0,
            "rings": [_flat(r) for r in rings],
        }
    print("water-only (fallback) nodes:", water_only)

    def wdx(a: float, b: float) -> float:
        d = abs(a - b) % W
        return min(d, W - d)

    routes = []
    for nid in node_ids:
        for og in as_list(tree[nid].get("outgoing")):
            ctrl = [float(x) for x in og["control"]]
            pts = [(c[0], H - c[1]) for c in zip(ctrl[0::2], ctrl[1::2])]
            ax, ay = nodes[nid]["anchor"]
            bx, by = nodes[og["name"]]["anchor"]

            def cost(seq):
                return (wdx(seq[0][0], ax) + abs(seq[0][1] - ay)
                        + wdx(seq[-1][0], bx) + abs(seq[-1][1] - by))

            if cost(pts[::-1]) < cost(pts):
                pts.reverse()
            # The game's control points are only the INTERMEDIATE bends of the
            # route (1-9 of them); the curve itself runs anchor -> controls -> anchor.
            pts = [(ax, ay)] + pts + [(bx, by)]
            # Pacific routes wrap around the map edge: unwrap x so the polyline is
            # continuous (x may leave [0, width]; the client draws a shifted copy).
            un = [pts[0]]
            for x, y in pts[1:]:
                px = un[-1][0]
                while x - px > W / 2:
                    x -= W
                while px - x > W / 2:
                    x += W
                un.append((x, y))
            routes.append({"from": nid, "to": og["name"], "points": [int(round(v)) for p in un for v in p]})

    check_against_graph(nodes, routes)
    return {
        "version": 1,
        "water_only_nodes": water_only,
        "width": W,
        "height": H,
        "land": [_flat(r) for r in land_rings],
        "nodes": nodes,
        "routes": routes,
    }


def check_against_graph(nodes: dict, routes: list) -> None:
    graph = json.loads(TRADENODES_JSON.read_text())
    gids = set(graph["nodes"])
    if gids != set(nodes):
        raise SystemExit(f"node mismatch vs tradenodes.json: {gids ^ set(nodes)}")
    gedges = {(nid, o["target"]) for nid, n in graph["nodes"].items() for o in n["outgoing"]}
    medges = {(r["from"], r["to"]) for r in routes}
    if gedges != medges:
        raise SystemExit(f"edge mismatch vs tradenodes.json: {gedges ^ medges}")


def render_preview(data: dict, path: str, scale: float = 0.25, crop=None) -> None:
    from PIL import ImageDraw

    W, H = data["width"], data["height"]
    cx0, cy0, cx1, cy1 = crop or (0, 0, W, H)
    s = scale
    img = Image.new("RGB", (int((cx1 - cx0) * s), int((cy1 - cy0) * s)), (20, 30, 50))
    dr = ImageDraw.Draw(img)

    def tr(flat):
        return [((flat[i] - cx0) * s, (flat[i + 1] - cy0) * s) for i in range(0, len(flat), 2)]

    for nid, n in data["nodes"].items():
        col = tuple(80 + (hash(nid + str(k)) % 150) for k in range(3))
        for r in n["rings"]:
            dr.polygon(tr(r), fill=col)
    for r in data["land"]:
        dr.line(tr(r) + tr(r)[:1], fill=(255, 255, 255), width=1)
    for rt in data["routes"]:
        dr.line(tr(rt["points"]), fill=(255, 220, 0), width=2)
    for nid, n in data["nodes"].items():
        x, y = tr(n["anchor"])[0]
        dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 0, 0))
        dr.text((x + 4, y - 4), nid, fill=(255, 255, 255))
    img.save(path)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    install = find_install(args[0] if args else None)
    data = build(install)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.2f} MB), "
          f"{len(data['nodes'])} nodes, {len(data['routes'])} routes, {len(data['land'])} land rings")
    if "--preview" in sys.argv:
        render_preview(data, "/tmp/map_preview.png")
        render_preview(data, "/tmp/map_preview_zoom.png", scale=1.0, crop=(2500, 150, 3700, 900))
        print("previews in /tmp/map_preview*.png")


if __name__ == "__main__":
    main()
