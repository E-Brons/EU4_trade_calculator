"""Alternatives that would also explain POR at S79 ohio/chesapeake_bay: C = A or (receives transferred power, t_in > 0, and does not collect here)."""
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
c = Counter(); rows = []
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
        pa = pc = 0.0; extra = []
        for (node, t), d in ents.items():
            if node != nid: continue
            eff = f(d.get("val")) - f(d.get("t_out")) + f(d.get("t_in"))
            ch = "total" in d or bool(d.get("has_capital")); s = "type" in d
            a = s or (not ch and bool(coll[t] & down(nid)))
            cc = a or (not ch and f(d.get("t_in")) > 0)
            pa += eff * a; pc += eff * cc
            if f(d.get("t_in")) > 0 and not ch: c["non-collecting receivers (t_in>0)"] += 1; c["  of which A already pulls"] += a
            if cc and not a: extra.append((t, round(eff, 3)))
        rp = f(n["pull_power"])
        if abs(pa - pc) > 0.0105:
            c["A!=C nodes"] += 1; c["  record follows C"] += abs(pc - rp) <= 0.0105; c["  record follows A"] += abs(pa - rp) <= 0.0105; rows.append((e["id"], nid, extra))
print(dict(c)); print(rows)
