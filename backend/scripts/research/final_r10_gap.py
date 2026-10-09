"""R10 final, part 1: node `total` versus the sum of the country `val` entries, over the whole corpus (independent code).

For every node instance with a `total`:
  sumval  = sum of `val` of all entries (PIR has none)
  gap     = total - sumval
  unc     = sum of province `trade_power` of the provinces of the node whose `controller` is REB or absent (credited to no entry)
  unc2    = same for provinces whose controller tag has no entry with province_power at that node  (superset check)
  ppc     = p_pow - sum(entry.province_power)      (power that is in p_pow but in no entry)
  classes: G0 |gap|<=TOL ; G1 |gap-unc|<=TOL ; G2 |gap-ppc|<=TOL (not G1) ; G3 residual (none of them)
Also: stale-aggregate detector (top_power tag without an entry), the identity p_pow == sum of province trade_power, num_collectors
pairs, PIR entry shapes, nodes without `total`, and retain/pull/collector_power recomputed from the entries (rule B of R03).
U01/U02 are copies of S80/S79: counted in "86 entries" and removed in "84 distinct saves".
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
from app.parsing.tradenodes import load_trade_graph  # noqa: E402

TAG = re.compile(r"^[A-Z0-9]{2,4}$")
TOL = 0.0035
COPIES = {"U01": "S80", "U02": "S79"}
G = load_trade_graph()
DOWN = {}


def down(n):
    if n not in DOWN:
        s = set()
        for t in G.outgoing(n):
            s.add(t)
            s |= down(t)
        DOWN[n] = s
    return DOWN[n]


def f(x):
    try:
        return float(x)
    except Exception:
        return 0.0


C = collections.Counter()          # all 86 entries
D = collections.Counter()          # 84 distinct saves (U01/U02 skipped)
resid = []                         # (save, node, residual, gap, unc, ppc)
only_ppc = []
p_pow_bad = collections.Counter()
nototal = collections.Counter()
pirshape = collections.Counter()
stale = []
noise = []                         # |gap| of G0 nodes
rp_fail = []                       # retain / pull recompute failures
tp_bad = []
entries_all = common.entries()
for e in entries_all:
    sid = e["id"]
    distinct = sid not in COPIES
    ps = common.block(e, "provinces")
    bynode = collections.defaultdict(list)
    for k, p in ps.items():
        if isinstance(p, dict) and "trade" in p:
            bynode[p["trade"]].append(p)
    ns = common.nodes(e)
    ents_by = {}
    for n in ns:
        ents_by[n["definitions"]] = {t: v for t, v in n.items() if TAG.match(t) and isinstance(v, dict)}
    collect = collections.defaultdict(set)
    steer = collections.defaultdict(set)
    for nid, ents in ents_by.items():
        for t, c in ents.items():
            if "total" in c or c.get("has_capital"):
                collect[t].add(nid)
            if "type" in c:
                steer[t].add(nid)
    for n in ns:
        nid = n["definitions"]
        ents = ents_by[nid]
        for cnt in ((C, D) if distinct else (C,)):
            cnt["node instances"] += 1
        pir = ents.get("PIR")
        pirshape[tuple(sorted(pir)) if pir is not None else None] += distinct
        # stale aggregate detector
        miss = (set(n.get("top_power") or []) | set(n.get("top_provinces") or [])) - set(ents)
        if miss:
            stale.append((sid, nid, sorted(miss)))
        # num_collectors pair
        if "num_collectors" in n and "num_collectors_including_pirates" in n:
            d = n["num_collectors_including_pirates"] - n["num_collectors"]
            dd = f(n.get("collector_power_including_pirates")) - f(n.get("collector_power"))
            if distinct:
                D["pair exists"] += 1
                D["ncp-nc == 1"] += d == 1
                D["cpp == cp (1e-9)"] += abs(dd) < 1e-9
        else:
            if distinct:
                D["pair absent"] += 1
                D["pair absent and total absent"] += "total" not in n
        if "total" not in n:
            nototal[(nid, "potential" in (pir or {}))] += distinct
            continue
        sumval = sum(f(v.get("val")) for v in ents.values())
        gap = n["total"] - sumval
        plist = bynode.get(nid, [])
        provsum = sum(f(p.get("trade_power")) for p in plist)
        unc = sum(f(p.get("trade_power")) for p in plist if p.get("controller") in (None, "REB"))
        credited = sum(f(v.get("province_power")) for v in ents.values())
        ppc = f(n.get("p_pow")) - credited
        if distinct:
            D["nodes with total"] += 1
            D["p_pow present"] += "p_pow" in n
            D["p_pow == sum province trade_power (0.002)"] += abs(provsum - f(n.get("p_pow"))) <= 0.002
            D["collector_power == retain_power (0.0015)"] += abs(f(n.get("collector_power")) - f(n.get("retain_power"))) <= 0.0015
        if abs(provsum - f(n.get("p_pow"))) > 0.002 and distinct:
            p_pow_bad[round(f(n.get("p_pow")) - provsum, 3)] += 1
        for cnt in ((C, D) if distinct else (C,)):
            if abs(gap) <= TOL:
                cnt["G0 gap=0"] += 1
                if cnt is D:
                    noise.append(abs(gap))
            elif abs(gap - unc) <= TOL:
                cnt["G1 gap == REB/uncontrolled province power"] += 1
            elif abs(gap - ppc) <= TOL:
                cnt["G2 gap == p_pow - sum(province_power) only"] += 1
                if cnt is D:
                    only_ppc.append((sid, nid, round(gap, 3), round(unc, 3), round(ppc, 3)))
            else:
                cnt["G3 residual"] += 1
                if cnt is D:
                    resid.append((sid, nid, round(gap - unc, 3), round(gap, 3), round(unc, 3), round(ppc, 3)))
        # retain / pull recomputation from the entries (rule B of R03)
        retain = 0.0
        pull = 0.0
        for t, c in ents.items():
            eff = f(c.get("val")) - f(c.get("t_out")) + f(c.get("t_in"))
            coll = "total" in c or bool(c.get("has_capital"))
            st = "type" in c
            if coll:
                retain += eff
            if st or (not coll and bool((collect[t] | steer[t]) & down(nid))):
                pull += eff
        gapnode = abs(gap) > TOL
        for cnt in ((C, D) if distinct else (C,)):
            if "retain_power" in n:
                cnt["retain nodes (gap)" if gapnode else "retain nodes (no gap)"] += 1
                if abs(retain - f(n["retain_power"])) <= 0.0105:
                    cnt["retain ok (gap)" if gapnode else "retain ok (no gap)"] += 1
                elif cnt is D:
                    rp_fail.append(("retain", sid, nid, round(retain, 3), n["retain_power"], round(retain - n["retain_power"], 3), gapnode))
            if "pull_power" in n and nid in G:
                cnt["pull nodes (gap)" if gapnode else "pull nodes (no gap)"] += 1
                if abs(pull - f(n["pull_power"])) <= 0.0105:
                    cnt["pull ok (gap)" if gapnode else "pull ok (no gap)"] += 1
                elif cnt is D:
                    rp_fail.append(("pull", sid, nid, round(pull, 3), n["pull_power"], round(pull - n["pull_power"], 3), gapnode))

print("entries", len(entries_all), "distinct saves", len(entries_all) - len(COPIES))
print("--- 86 entries"); [print(" ", v, k) for k, v in sorted(C.items())]
print("--- 84 distinct saves"); [print(" ", v, k) for k, v in sorted(D.items())]
print("max |gap| among G0 nodes:", max(noise), " | G0 count", len(noise))
print("PIR entry shapes (distinct):", dict(pirshape))
print("nodes without total (distinct) by (node, PIR has potential):", dict(nototal))
print("p_pow != sum province trade_power: by (p_pow - provsum) rounded:", sorted(p_pow_bad.items(), key=lambda a: -a[1])[:12], "n", sum(p_pow_bad.values()))
print("stale-aggregate detector (top_power/top_provinces tag with no entry):", stale)
print("G2 nodes:", only_ppc)
print("retain/pull failures (recomputed from entries):", len(rp_fail))
for r in rp_fail:
    print("  ", r)
print("G3 residual nodes:", len(resid), "positive", sum(r[2] > 0 for r in resid), "negative", sum(r[2] < 0 for r in resid))
for r in sorted(resid, key=lambda r: (r[0], r[2], r[1])):
    print("  ", r)
json.dump(dict(resid=resid, g2=only_ppc, stale=stale, rp_fail=rp_fail), open("/tmp/eu4research/final_r10_gap.json", "w"))
