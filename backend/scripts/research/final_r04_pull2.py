"""R04 final, script 4: for the 60 receiver entries (non-collecting, non-steering, no collection downstream) what else distinguishes
the 4 counted (POR S79/U02) from the 56 not counted (SPA, BRZ): collects anywhere / steers anywhere / steers downstream."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r04_common as F
from app.parsing.tradenodes import load_trade_graph
G = load_trade_graph()
DOWN = {}
def down(n):
    if n not in DOWN:
        s = set()
        for t in G.outgoing(n): s.add(t); s |= down(t)
        DOWN[n] = s
    return DOWN[n]
rows = Counter(); ex = []
for sid, e, nodes in F.saves():
    ents = {}
    for n in nodes:
        for tag, c in F.entries_of(n).items():
            if set(c) - {"max_demand"}: ents[(n["definitions"], tag)] = c
    coll = defaultdict(set); steer = defaultdict(set); merch = defaultdict(set)
    for (nid, tag), c in ents.items():
        if "total" in c or c.get("has_capital"): coll[tag].add(nid)
        if "type" in c: steer[tag].add(nid)
        if "has_trader" in c: merch[tag].add(nid)
    for n in nodes:
        nid = n["definitions"]
        if "pull_power" not in n or nid not in G: continue
        for tag, c in F.entries_of(n).items():
            if "t_in" in c and not ("total" in c or c.get("has_capital")) and "type" not in c and not (coll[tag] & down(nid)):
                counted = bool(steer[tag] & down(nid))
                key = (tag, "counted(B)" if counted else "not counted", "collects_anywhere=%s" % bool(coll[tag]), "steers_anywhere=%s" % bool(steer[tag]), "has_trader_here=%s" % ("has_trader" in c))
                rows[key] += 1
                ex.append((sid, nid, tag, counted, sorted(steer[tag])[:6], sorted(coll[tag])))
for k, v in sorted(rows.items()): print(v, k)
seen = set()
for x in ex:
    k = (x[2], x[3])
    if k in seen: continue
    seen.add(k); print("example", x)
