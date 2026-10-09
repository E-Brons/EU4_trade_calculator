"""R11 final (4/5): where the power of a ship goes (pool class of ship entries) and the closed-form money of one more ship at a collecting node.
Independent code (raw save keys only)."""
import sys, math, statistics
sys.path.insert(0, "scripts/research")
import final_r11_lib as L
from collections import Counter, defaultdict

G = L.GRAPH
DOWN = {}
def down(n):
    if n not in DOWN:
        st = set()
        for o in G[n]["outgoing"]:
            st.add(o["target"]); st |= down(o["target"])
        DOWN[n] = st
    return DOWN[n]
for n in G: down(n)

def fx(x): return math.trunc(x * 1000 + 1e-9) / 1000.0
def eff(c): return L.fnum(c.get("val")) - L.fnum(c.get("t_out")) + L.fnum(c.get("t_in"))

# ---- (a) share identity over the whole corpus (all 84 distinct saves): total = fx(current * power_fraction), power_fraction = fx(eff/retain)
ident = Counter(); bad = []
for s in L.saves():
    for (tag, node), c in s.ent.items():
        if "total" not in c: continue
        n = s.node_by_id[node]
        cur, ret = L.fnum(n.get("current")), L.fnum(n.get("retain_power"))
        if ret <= 0 or "power_fraction" not in c: continue
        ident["collectors"] += 1
        pf = fx(eff(c) / ret)
        if abs(pf - L.fnum(c["power_fraction"])) <= 0.0011: ident["pf_ok"] += 1
        t = L.fnum(c["total"])
        if abs(fx(cur * L.fnum(c["power_fraction"])) - t) <= 0.0011: ident["total_ok"] += 1
        elif len(bad) < 10: bad.append((s.id, tag, node, t, round(fx(cur * L.fnum(c["power_fraction"])), 3)))
print("(a) collecting entries with power_fraction:", ident["collectors"], " power_fraction == fx(eff/retain_power):", ident["pf_ok"], " total == fx(current*power_fraction):", ident["total_ok"])
print("    first exceptions of the second identity:", bad)

# ---- (b) pool class of ship entries
cls_n = Counter(); cls_p = Counter()
rowsB = []
for s in L.saves():
    if not L.has_ships(s): continue
    coll = defaultdict(set); steer = defaultdict(set)
    for (tag, node), c in s.ent.items():
        if "total" in c or c.get("has_capital"): coll[tag].add(node)
        if "type" in c: steer[tag].add(node)
    for (tag, node), c in s.ent.items():
        if "light_ship" not in c: continue
        collects = "total" in c or bool(c.get("has_capital")); st = "type" in c
        if collects: k = "collects (retain_power)"
        elif st: k = "steers (pull_power)"
        elif (coll[tag] | steer[tag]) & down(node): k = "pulls by downstream collect/steer (pull_power)"
        else: k = "not counted (no pool)"
        endn = not G[node]["outgoing"]
        cls_n[k] += 1; cls_p[k] += L.fnum(c["ship_power"])
        rowsB.append((s.id, tag, node, k, endn))
print("(b) ship entries by pool class (all ticked saves, copies excluded):")
for k in cls_n: print("    ", k, cls_n[k], "entries, ship_power sum %.1f" % cls_p[k])
print("    not-counted ship entries at end nodes:", sum(1 for r in rowsB if r[3].startswith("not counted") and r[4]), " TUR not-counted:", [(r[0], r[2]) for r in rowsB if r[1] == "TUR" and r[3].startswith("not counted")])
print("    ship entries at an end node:", sum(1 for r in rowsB if r[4]), " of which collects:", sum(1 for r in rowsB if r[4] and r[3].startswith("collects")))

# ---- (c) closed form: one more frigate (power f*3.5) at a collecting entry; money' = money * share'/share, share = gross*eff/(retain+pull)
print("(c) one more frigate at a collecting ship entry (closed form; others held fixed; downstream flow change ignored):")
allv = []
for s in L.saves():
    if not L.has_ships(s): continue
    for (tag, node), c in s.ent.items():
        if "light_ship" not in c or "total" not in c or "money" not in c: continue
        n = s.node_by_id[node]
        ret, pul = L.fnum(n.get("retain_power")), L.fnum(n.get("pull_power"))
        cur, rt = L.fnum(n.get("current")), L.fnum(n.get("retention"))
        if ret <= 0 or rt <= 0: continue
        gross = cur / rt
        sp, ns = L.fnum(c["ship_power"]), int(L.fnum(c["light_ship"]))
        f = sp / (ns * 3.3) if ns else 1.0
        d = 3.5 * L.fnum(c.get("max_demand"))               # f = 1 assumed for the quoted TUR rows
        e = eff(c); money = L.fnum(c["money"])
        share0 = gross * e / (ret + pul); share1 = gross * (e + d) / (ret + pul + d)
        dm = money * (share1 / share0 - 1) if share0 > 0 else 0
        # removing all the entry's ships
        e2 = e - L.fnum(c["val"]) * (sp / L.fnum(c["max_pow"]))   # val share of ship_power = val * ship_power/max_pow
        share2 = gross * e2 / (ret + pul - (e - e2))
        dm_all = money * (share2 / share0 - 1)
        allv.append((s.id, tag, node, ns, round(dm, 3), round(dm_all, 2)))
tur = [r for r in allv if r[1] == "TUR"]
for r in tur: print("    ", r)
print("    all collecting ship entries:", len(allv), " +1 frigate: median %.3f  min %.3f  max %.3f" % (statistics.median(r[4] for r in allv), min(r[4] for r in allv), max(r[4] for r in allv)))
print("    all positive:", all(r[4] > 0 for r in allv))
