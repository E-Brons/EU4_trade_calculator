"""R04 final, script 3: pull_power membership of transfer receivers (POR case), rule A (collect downstream) vs B (collect or steer downstream)
vs C (receiving counts). Independent of app.trade.calc; only the link graph is read from app.parsing.tradenodes."""
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
        for t in G.outgoing(n):
            s.add(t); s |= down(t)
        DOWN[n] = s
    return DOWN[n]
for n in G.nodes: down(n)

tot = Counter(); dist = Counter(); exc = defaultdict(list)
recv_rows = []
for sid, e, nodes in F.saves():
    dup = sid in F.COPY_OF
    ents = {}
    for n in nodes:
        for tag, c in F.entries_of(n).items():
            if set(c) - {"max_demand"}:
                ents[(n["definitions"], tag)] = c
    coll = defaultdict(set); steer = defaultdict(set)
    for (nid, tag), c in ents.items():
        if "total" in c or c.get("has_capital"): coll[tag].add(nid)
        if "type" in c: steer[tag].add(nid)
    C = Counter()
    byn = defaultdict(list)
    for (nid, tag), c in ents.items(): byn[nid].append((tag, c))
    for n in nodes:
        nid = n["definitions"]
        if "pull_power" not in n or nid not in G: continue
        rec = F.m(n["pull_power"])
        pa = pb = pc = 0
        has_recv = False
        for tag, c in byn[nid]:
            eff = (F.m(c["val"]) if "val" in c else 0) - (F.m(c["t_out"]) if "t_out" in c else 0) + (F.m(c["t_in"]) if "t_in" in c else 0)
            here_c = "total" in c or bool(c.get("has_capital")); st = "type" in c
            a = st or (not here_c and bool(coll[tag] & down(nid)))
            b = st or (not here_c and bool((coll[tag] | steer[tag]) & down(nid)))
            cc = b or (not here_c and "t_in" in c)
            pa += eff * a; pb += eff * b; pc += eff * cc
            if "t_in" in c:
                has_recv = True
                if not here_c and not st:
                    kind = "collect_down" if (coll[tag] & down(nid)) else ("steer_down_only" if (steer[tag] & down(nid)) else "no_action_down")
                    C["recv_noncoll_nonsteer_" + kind] += 1
                    recv_rows.append((sid, nid, tag, kind, eff))
                    if not dup: dist["recv_noncoll_nonsteer_" + kind] += 0
                elif here_c: C["recv_collecting"] += 1
                else: C["recv_steering"] += 1
        C["pull_nodes"] += 1
        okA = abs(pa - rec) <= 10; okB = abs(pb - rec) <= 10; okC = abs(pc - rec) <= 10
        C["A_ok"] += okA; C["B_ok"] += okB; C["C_ok"] += okC
        if not okA: exc["A"].append((sid, nid, rec / 1000, pa / 1000))
        if not okB: exc["B"].append((sid, nid, rec / 1000, pb / 1000))
        if not okC: exc["C"].append((sid, nid, rec / 1000, pc / 1000))
        if abs(pa - pb) > 10: C["A_ne_B_nodes"] += 1
        if abs(pb - pc) > 10: C["B_ne_C_nodes"] += 1
        if has_recv:
            C["pull_nodes_with_receiver"] += 1; C["B_ok_with_receiver"] += okB; C["A_ok_with_receiver"] += okA; C["C_ok_with_receiver"] += okC
    tot.update(C)
    if not dup: dist.update(C)
for nm, c in (("ALL 86 entries", tot), ("84 DISTINCT", dist)):
    print("==", nm)
    for k in sorted(c): print(f"  {k}: {c[k]}")
for k, v in exc.items():
    print("EXC rule", k, len(v))
    for x in v[:12]: print("   ", x)
print("receivers (non-collecting, non-steering) with no downstream collection, by (tag, kind) across all 86 entries:")
cnt = Counter((r[2], r[3], ) for r in recv_rows if r[3] != "collect_down")
for k, v in sorted(cnt.items()): print("  ", k, v)
print("saves/nodes of steer_down_only:", [(r[0], r[1], r[2], round(r[4] / 1000, 3)) for r in recv_rows if r[3] == "steer_down_only"])
print("distinct-save totals of kinds:", Counter(r[3] for r in recv_rows if r[0] not in F.COPY_OF))
