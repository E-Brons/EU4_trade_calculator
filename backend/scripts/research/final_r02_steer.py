"""R02 final, test 2: are steering entries away from the home node, and merchants without an action, halved?
Ratio of max_demand to the same country's passive, merchant-free, embargo-clean baseline of the same class (dom/for).
Entries considered: embargo-clean only (no embargoer with own power at the node). Steering entries at the node of
trade_port are excluded (home bonus, R01). Usage: .venv/bin/python scripts/research/final_r02_steer.py"""
import statistics
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r02_lib as L

TOL = 0.0011


def klass(s, nid, tag):
    return "dom" if (s["nodes"][nid]["top"] == tag or nid == L.port_node(s, tag)) else "for"


def passive(e):
    return not (e["trader"] or e["steer"] or e["coll"] or e["cap"]) and e["md"] is not None


res = defaultdict(Counter)
exc = defaultdict(list)
for sid, s in L.all_saves():
    base = defaultdict(list)
    for nid, n in s["nodes"].items():
        for tag, e in n["e"].items():
            if passive(e) and not L.embargo_active(s, nid, tag):
                base[(tag, klass(s, nid, tag))].append(e["md"])
    for nid, n in s["nodes"].items():
        pn_cache = {}
        for tag, e in n["e"].items():
            if e["md"] is None or L.embargo_active(s, nid, tag) or e["cap"] or e["coll"]:
                continue
            kind = "steer-away" if e["steer"] else ("merchant-no-action" if e["trader"] else None)
            if kind is None:
                continue
            if nid == L.port_node(s, tag):
                res[kind]["at home node (excluded)"] += 1
                continue
            b = base.get((tag, klass(s, nid, tag)), [])
            if not b:
                res[kind]["no baseline"] += 1
                continue
            bm = statistics.median(b)
            r = e["md"] / bm
            if abs(e["md"] - bm) <= TOL:
                res[kind]["= baseline (ratio 1)"] += 1
            elif abs(e["md"] - 0.5 * bm) <= TOL:
                res[kind]["= 0.5 x baseline"] += 1
                exc[kind].append((sid, nid, tag, e["md"], bm, round(r, 4), "HALVED"))
            else:
                res[kind]["other"] += 1
                exc[kind].append((sid, nid, tag, e["md"], bm, round(r, 4), "other"))
for kind in ("steer-away", "merchant-no-action"):
    print(kind, dict(res[kind]), "| compared:", sum(v for k, v in res[kind].items() if k in ("= baseline (ratio 1)", "= 0.5 x baseline", "other")))
    rs = [x[5] for x in exc[kind]]
    print("  non-baseline entries:", len(exc[kind]), "ratio min/max", (min(rs), max(rs)) if rs else None,
          "halved:", sum(1 for x in exc[kind] if x[6] == "HALVED"))
    cnt = Counter((x[0], x[2]) for x in exc[kind])
    print("  by (save, tag):", dict(sorted(cnt.items())))
    for x in exc[kind][:40]:
        print("    ", x)
