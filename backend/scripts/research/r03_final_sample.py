"""Goal's worked examples (xian, hormuz) and the 40-row labelled sample re-checked against the real saves; already_sent vs membership."""
import sys, re
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
E = {e["id"]: e for e in common.entries()}
sample = """S11 timbuktu SOS included
S18 valencia LUC included
S46 baltic_sea LIT EXCLUDED
S11 lahore SHY EXCLUDED
S19 comorin_cape HDR included
S33 comorin_cape ADE included
S49 beijing CHG included
S73 ganges_delta NAG included
S23 kiev GOL EXCLUDED
S04 tunis MLO included
S53 alexandria FRA included
S05 timbuktu BEN included
S12 astrakhan GEN included
S49 astrakhan TUR included
S75 alexandria ANZ EXCLUDED
S59 yumen QNG EXCLUDED
S55 timbuktu AIR EXCLUDED
S45 north_sea BRE included
S70 ivory_coast POR EXCLUDED
S51 lubeck BRA EXCLUDED
S09 kiev GOL EXCLUDED
S34 valencia LAN included
S53 tunis TUS included
S14 lahore VIJ EXCLUDED
S60 siberia ZUN EXCLUDED
S67 baltic_sea PRU EXCLUDED
S10 ragusa URB included
S49 ragusa FER included
S36 ivory_coast KON EXCLUDED
S09 ragusa BYZ EXCLUDED
S58 astrakhan KZH EXCLUDED
S13 tunis PRO EXCLUDED
S07 lubeck BRA EXCLUDED
S11 tunis MOR EXCLUDED
S24 ragusa GEN included
S48 beijing OIR included
S10 comorin_cape AJU included
S76 saxony FRA included
S14 rheinland SWE EXCLUDED
S32 rheinland HAB EXCLUDED
S04 gulf_of_aden SFA included
S71 lubeck NOR EXCLUDED
S47 gujarat MLI included"""
cache = {}
def world(sid):
    if sid not in cache:
        nodes = common.nodes(E[sid]); ents = {}
        for n in nodes:
            for t, d in n.items():
                if isinstance(d, dict) and len(t) <= 4 and t.upper() == t and set(d) - {"max_demand"}: ents[(n["definitions"], t)] = d
        coll = defaultdict(set); st = defaultdict(set)
        for (node, t), d in ents.items():
            if "total" in d or d.get("has_capital"): coll[t].add(node)
            if "type" in d: st[t].add(node)
        cache[sid] = (ents, coll, st, {n["definitions"]: n for n in nodes})
    return cache[sid]
res = Counter(); bad = []
for line in sample.split("\n"):
    sid, node, tag, label = line.split()
    ents, coll, st, nodes = world(sid)
    d = ents.get((node, tag))
    if d is None: res["row not found"] += 1; bad.append((line, "no entry")); continue
    ch = "total" in d or bool(d.get("has_capital")); s = "type" in d
    a = s or (not ch and bool(coll[tag] & down(node)))
    b = s or (not ch and bool((coll[tag] | st[tag]) & down(node)))
    want = label == "included"
    res["found"] += 1
    res["A agrees with label"] += (a == want); res["B agrees with label"] += (b == want)
    if a != want or b != want: bad.append((line, "A", a, "B", b, "collects at", sorted(coll[tag])[:4], "steers at", sorted(st[tag])[:3]))
print(dict(res))
for b in bad: print(b)
# worked examples: find the nodes by recorded retain/pull
for sid in E:
    ents, coll, st, nodes = world(sid)
    for nid, n in nodes.items():
        if nid in ("xian", "hormuz") and n.get("pull_power") is not None and (abs(f(n["pull_power"]) - 56.459) < 0.002 or abs(f(n["pull_power"]) - 363.19) < 0.002):
            print("worked example found:", sid, nid, "retain", n.get("retain_power"), "pull", n.get("pull_power"), "total", n.get("total"))
            members = []
            for (node, t), d in ents.items():
                if node != nid: continue
                eff = f(d.get("val")) - f(d.get("t_out")) + f(d.get("t_in"))
                ch = "total" in d or bool(d.get("has_capital")); s = "type" in d
                a = s or (not ch and bool(coll[t] & down(nid))); b = s or (not ch and bool((coll[t] | st[t]) & down(nid)))
                role = "collecting" if ch else ("steering" if s else "other")
                if eff > 1: members.append((t, role, round(eff, 3), "pull A" if a else "excluded", "pull B" if b else "excl B"))
            for m in sorted(members, key=lambda x: -x[2])[:14]: print("   ", m)
# already_sent vs membership (distinct saves)
c = Counter()
for sid in E:
    if sid in ("U01", "U02"): continue
    ents, coll, st, nodes = world(sid)
    for (node, t), d in ents.items():
        if nodes[node].get("pull_power") is None: continue
        ch = "total" in d or bool(d.get("has_capital")); s = "type" in d
        a = s or (not ch and bool(coll[t] & down(node)))
        key = "with already_sent" if "already_sent" in d else "without"
        kind = "collect" if ch else ("steer" if s else ("pull" if a else "excluded"))
        c[(key, kind)] += 1
for k in sorted(c): print(k, c[k])
