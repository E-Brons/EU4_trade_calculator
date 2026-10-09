"""R02 final: how many distinct countries / (country,node) pairs / saves carry the 188 half-matches, and do start saves contain any away collector?"""
import sys
from collections import Counter
sys.path.insert(0, "scripts/research")
import common, final_r02_core as core

per_save_half, pairs, tags = Counter(), set(), set()
start_away = 0
for e in common.entries():
    sid = e["id"]
    if sid in core.DUPLICATES:
        continue
    nodes, countries = core.load(e)
    res, exc, d = core.per_save(e)
    away_all = sum(1 for tag, byn in d["rows"].items() for n, x in byn.items() if core.classify(x, n, d["homes"].get(tag)) == "away_collect")
    if sid not in core.CAMPAIGN:
        start_away += away_all
        continue
    rws, homes, clean = d["rows"], d["homes"], d["clean"]
    for tag, byn in rws.items():
        for n, x in byn.items():
            if core.classify(x, n, homes.get(tag)) != "away_collect" or not clean(tag, n):
                continue
            md = float(x["max_demand"])
            others = [float(y["max_demand"]) for n2, y in byn.items() if n2 != n and core.classify(y, n2, homes.get(tag)) != "away_collect" and clean(tag, n2)]
            if any(abs(md - 0.5 * b) <= core.TOL for b in others):
                per_save_half[sid] += 1; pairs.add((tag, n)); tags.add(tag)
print("half-matches per campaign save:", dict(per_save_half), "total", sum(per_save_half.values()))
print("distinct countries:", len(tags), "distinct (country,node) pairs:", len(pairs))
print("away collectors in the 78 start saves (all, incl. embargoed):", start_away)
