"""R03 final: independent whole-corpus test of the pull_power rule (A: R03 wiki rule; B: steering downstream also counts).
Recomputes pull_power / retain_power / retention per node from raw save keys (no app.trade.calc code)."""
import sys, json
from collections import defaultdict
sys.path.insert(0, "scripts/research")
import common
from app.parsing.tradenodes import load_trade_graph

G = load_trade_graph()
DOWN = {}
def down(n):
    if n not in DOWN:
        s = set()
        for t in G.outgoing(n):
            s.add(t); s |= down(t)
        DOWN[n] = s
    return DOWN[n]
for n in G.nodes: down(n)

def f(x):
    try: return float(x)
    except Exception: return 0.0

stats = defaultdict(lambda: defaultdict(int))
mism = {"A": [], "B": []}
ret_bad = {"A": 0, "B": 0}
rows_out = []
for e in common.entries():
    sid = e["id"]
    nodes = common.nodes(e)
    ents = {}      # (node, tag) -> dict
    for n in nodes:
        for tag, c in n.items():
            if isinstance(c, dict) and len(tag) <= 4 and tag.upper() == tag and (set(c) - {"max_demand"}):
                ents[(n["definitions"], tag)] = c
    collect = defaultdict(set); steer = defaultdict(set)
    for (node, tag), c in ents.items():
        if "total" in c or c.get("has_capital"): collect[tag].add(node)
        if "type" in c: steer[tag].add(node)
    for n in nodes:
        nid = n["definitions"]
        if nid not in G: continue
        rec_pull = n.get("pull_power"); rec_ret = n.get("retain_power")
        retain = 0.0; pull = {"A": 0.0, "B": 0.0}; who = {"A": [], "B": []}
        for (node, tag), c in ents.items():
            if node != nid: continue
            eff = f(c.get("val")) - f(c.get("t_out")) + f(c.get("t_in"))
            coll_here = "total" in c or bool(c.get("has_capital"))
            st = "type" in c
            if coll_here: retain += eff
            a = st or (not coll_here and bool(collect[tag] & down(nid)))
            b = st or (not coll_here and bool((collect[tag] | steer[tag]) & down(nid)))
            if a: pull["A"] += eff; who["A"].append(tag)
            if b: pull["B"] += eff; who["B"].append(tag)
        if rec_ret is not None:
            stats[sid]["retain_nodes"] += 1
            if abs(retain - f(rec_ret)) <= 0.0105: stats[sid]["retain_ok"] += 1
        if rec_pull is None: continue
        rp = f(rec_pull)
        stats[sid]["pull_nodes"] += 1
        for r in ("A", "B"):
            d = pull[r] - rp
            if abs(d) <= 0.0105: stats[sid][f"{r}_ok"] += 1
            else: mism[r].append((sid, nid, round(pull[r], 3), rp, round(d, 3)))
            if abs(d) <= 0.0005: stats[sid][f"{r}_exact"] += 1
            tot = retain + pull[r]
            rr = retain / tot if tot > 0 else 1.0
            if n.get("retention") is not None and abs(rr - f(n["retention"])) > 0.0011: ret_bad[r] += 1

tot = defaultdict(int)
for sid, s in stats.items():
    for k, v in s.items(): tot[k] += v
print("saves", len(stats))
print("pull nodes", tot["pull_nodes"], "| A within 0.0105:", tot["A_ok"], "exact(0.0005):", tot["A_exact"], "| B within 0.0105:", tot["B_ok"], "exact(0.0005):", tot["B_exact"])
print("retain nodes", tot["retain_nodes"], "retain within 0.0105:", tot["retain_ok"])
print("retention off (>0.0011) under A:", ret_bad["A"], "under B:", ret_bad["B"])
for r in ("A", "B"):
    print(f"--- rule {r}: {len(mism[r])} mismatching nodes")
    for m in mism[r]: print(m)
json.dump({"stats": {k: dict(v) for k, v in stats.items()}, "mism": mism}, open("/tmp/eu4research/r03_final_verify.json", "w"))
