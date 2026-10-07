"""R08 Q5: steering weights of trade nodes where no merchant steers. Run from backend/:
    .venv/bin/python scripts/research/r08_no_steerer_weights.py [--rebuild]
Pass 1 (cached in /tmp/r08_nosteer.json) extracts, for every node of the clean corpus (corpus.selected()) without any
steering entry, the recorded weights, the outgoing targets and every country entry (val, t_out, t_in, collecting,
has_capital, has_trader) plus each country's collecting / capital / steering nodes. Pass 2 tests the hypotheses."""
from __future__ import annotations

import math
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.trade import calc, corpus, game_data  # noqa: E402

CACHE = Path("/tmp/r08_nosteer.json")


def extract() -> list[dict]:
    graph = game_data.graph()
    rows = []
    for entry, world in corpus.iter_worlds(corpus.selected()):
        inp, rec = world.inputs, world.recorded
        collect, steer = defaultdict(set), defaultdict(set)
        for (node, tag), e in inp.entries.items():
            if e.collecting or e.has_capital:
                collect[tag].add(node)
            if e.steering:
                steer[tag].add(node)
        steered = {node for (node, _t), e in inp.entries.items() if e.steering}
        for node, nr in rec.nodes.items():
            targets = graph.outgoing(node)
            if len(targets) < 2 or not nr.steer_weights or node in steered:
                continue
            ents = []
            for (n, tag), e in inp.entries.items():
                if n != node:
                    continue
                r = rec.entries[(n, tag)]
                ents.append(dict(tag=tag, val=r.val or 0.0, t_out=e.t_out, t_in=e.t_in, collecting=e.collecting,
                                 has_capital=e.has_capital, has_trader=e.has_trader, province_power=e.province_power,
                                 ship_power=e.ship_power))
            rows.append(dict(save=entry["id"], series=entry.get("series"), date=entry.get("date"), node=node,
                             targets=list(targets), weights=list(nr.steer_weights), entries=ents,
                             collect={t: sorted(collect[t]) for t in {x["tag"] for x in ents}},
                             steer={t: sorted(steer[t]) for t in {x["tag"] for x in ents}},
                             pull_power=nr.pull_power, retain_power=nr.retain_power))
    return rows


def dist(graph, src: str, goals: set[str]) -> int | None:
    """shortest number of links from src to any goal (src itself excluded unless reached again)."""
    frontier, seen, d = [src], {src}, 0
    while frontier:
        d += 1
        nxt = []
        for n in frontier:
            for t in graph.outgoing(n):
                if t in goals:
                    return d
                if t not in seen:
                    seen.add(t)
                    nxt.append(t)
        frontier = nxt
    return None


def score(rows, predict, label):
    exact = near = nan = 0
    bad = []
    for r in rows:
        p = predict(r)
        if p is None or any(math.isnan(x) for x in p):
            nan += 1
            continue
        err = max(abs(a - b) for a, b in zip(p, r["weights"]))
        if err <= 0.001 + 1e-9:
            exact += 1
        if err <= 0.05:
            near += 1
        else:
            bad.append((r["save"], r["node"], tuple(round(x, 3) for x in p), r["weights"]))
    n = len(rows)
    print(f"{label:60s} exact {exact}/{n}  within 0.05 {near}/{n}  no prediction {nan}")
    return bad


def main():
    if "--rebuild" in sys.argv or not CACHE.exists():
        rows = extract()
        CACHE.write_text(json.dumps(rows))
    rows = json.loads(CACHE.read_text())
    graph = game_data.graph()
    print(f"{len(rows)} no-steerer nodes with >= 2 links in {len({r['save'] for r in rows})} saves")
    shape = Counter()
    for r in rows:
        w = r["weights"]
        shape["one-hot" if max(w) == 1.0 else "uniform" if len(set(w)) == 1 else "other"] += 1
    print("recorded shapes:", dict(shape))

    def pullers(r, use_steer=True):
        """countries that do not collect here but collect (or steer) downstream -> link index of the nearest such node."""
        out = []
        for e in r["entries"]:
            if e["collecting"] or e["has_capital"]:
                continue
            goals = set(r["collect"][e["tag"]]) | (set(r["steer"][e["tag"]]) if use_steer else set())
            goals.discard(r["node"])
            best = None
            for i, t in enumerate(r["targets"]):
                d = 0 if t in goals else dist(graph, t, goals)
                if d is not None and (best is None or d < best[0]):
                    best = (d, i)
            if best is not None:
                out.append((best[1], e))
        return out

    def eff(e):
        return e["val"] - e["t_out"] + e["t_in"]

    def h_pull(r, use_steer=True, power=eff):
        per = [0.0] * len(r["targets"])
        for i, e in pullers(r, use_steer):
            per[i] += power(e)
        s = sum(per)
        if s <= 0:
            return tuple(1.0 / len(per) for _ in per)
        return tuple(x / s for x in per)

    bad = score(rows, h_pull, "H1 pullers' effective power toward nearest collecting/steering node")
    score(rows, lambda r: h_pull(r, False), "H1b same, collecting nodes only")
    score(rows, lambda r: h_pull(r, True, lambda e: e["val"]), "H1c pullers' val")
    score(rows, lambda r: tuple(1.0 / len(r["targets"]) for _ in r["targets"]), "H0 uniform always")
    print("H1 counter-examples (first 12):")
    for b in bad[:12]:
        print("  ", b)
    # carry-over: same series, same node, previous save
    by = {(r["series"], r["node"], r["date"]): r for r in rows}
    same = diff = 0
    for r in rows:
        prevs = [k for k in by if k[0] == r["series"] and k[1] == r["node"] and k[2] < r["date"]]
        if prevs:
            p = by[max(prevs)]
            if max(abs(a - b) for a, b in zip(p["weights"], r["weights"])) <= 0.001:
                same += 1
            else:
                diff += 1
    print(f"carry-over between consecutive saves of a series (node unsteered in both): same {same}, different {diff}")
    # independent games: one weight tuple per node across all 1444 series?
    byn = defaultdict(set)
    for r in rows:
        byn[r["node"]].add((r["series"] == "tur-campaign", tuple(r["weights"])))
    multi = {n: v for n, v in byn.items() if len({w for t, w in v if not t}) > 1}
    print(f"nodes whose unsteered weights differ between independent 1444 games: {len(multi)}")
    # bookmark state (U07 VEN 1444.11.11, saved before the first computation; zip from git LFS, path as argument)
    book_path = next((a for a in sys.argv[1:] if a.endswith(".eu4")), None)
    if book_path:
        import re
        t = Path(book_path).read_text(encoding="latin-1")
        book = {}
        for m in re.finditer(r'\n\tnode=\{\n\t\tdefinitions="(\w+)"', t):
            blk = t[m.start():t.find("\n\t}", m.start() + 5)]
            book[m.group(1)] = tuple(float(x) for x in re.findall(r"\n\t\tsteer_power=([\d.]+)", blk))
        seen, eq, ne = set(), 0, 0
        for r in rows:
            if r["series"] == "tur-campaign" or (r["node"], r["series"]) in seen:
                continue
            seen.add((r["node"], r["series"]))
            b = book.get(r["node"], ())
            ok = len(b) == len(r["weights"]) and max(abs(x - y) for x, y in zip(b, r["weights"])) <= 0.001
            eq, ne = eq + ok, ne + (not ok)
        print(f"1444 unsteered (node, series) pairs equal to the bookmark weights: {eq} of {eq + ne}")


if __name__ == "__main__":
    main()
