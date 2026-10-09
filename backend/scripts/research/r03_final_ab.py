"""Where do rules A and B differ, and which one does the record follow? Also: has_trader entries with neither type nor total."""
import sys
sys.path.insert(0, "scripts/research")
import common
from collections import defaultdict, Counter
from app.parsing.tradenodes import load_trade_graph
G = load_trade_graph(); DOWN = {}
def down(n):
    if n not in DOWN:
        s = set()
        for t in G.outgoing(n): s.add(t); s |= down(t)
        DOWN[n] = s
    return DOWN[n]
for n in G.nodes: down(n)
def f(x):
    try: return float(x)
    except Exception: return 0.0
c = Counter(); diffs = []; noact = Counter()
for e in common.entries():
    if e["id"] in ("U01", "U02"): continue
    nodes = common.nodes(e); ents = {}
    for n in nodes:
        for t, d in n.items():
            if isinstance(d, dict) and len(t) <= 4 and t.upper() == t and set(d) - {"max_demand"}: ents[(n["definitions"], t)] = d
    coll = defaultdict(set); st = defaultdict(set)
    for (node, t), d in ents.items():
        if "total" in d or d.get("has_capital"): coll[t].add(node)
        if "type" in d: st[t].add(node)
    for n in nodes:
        nid = n["definitions"]
        if n.get("pull_power") is None: continue
        pa = pb = 0.0; extra = []
        for (node, t), d in ents.items():
            if node != nid: continue
            eff = f(d.get("val")) - f(d.get("t_out")) + f(d.get("t_in"))
            ch = "total" in d or bool(d.get("has_capital")); s = "type" in d
            a = s or (not ch and bool(coll[t] & down(nid)))
            b = s or (not ch and bool((coll[t] | st[t]) & down(nid)))
            pa += eff * a; pb += eff * b
            if b and not a: extra.append((t, round(eff, 3), sorted(st[t] & down(nid))[:2]))
            # merchants without an action
            if d.get("has_trader") and not s and not ch:
                noact["entries"] += 1; noact["pulling_by_A"] += a; noact["not_pulling_by_A"] += (not a)
        rp = f(n["pull_power"]); c["nodes"] += 1
        if abs(pa - pb) > 0.0105:
            c["A!=B nodes"] += 1
            c["  record follows A"] += abs(pa - rp) <= 0.0105
            c["  record follows B"] += abs(pb - rp) <= 0.0105
            diffs.append((e["id"], nid, extra, round(pa, 3), round(pb, 3), rp))
print(dict(c)); print("merchant without action (has_trader, no type, no total/home):", dict(noact))
for d in diffs: print(d)
