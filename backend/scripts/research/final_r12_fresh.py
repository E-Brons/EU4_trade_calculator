"""R12 final, script 3: freshness of the stored country entries against the live province values of the same save.
Signature tested:  entry.province_power == sum of province `trade_power` over the provinces with  controller == tag  in that node
(exact, thousandths).  A save in which this holds for every entry was written right after the entries were computed; a save in which
it fails for a fraction of entries carries entries computed earlier than the province values.  Run from backend/."""
import sys
sys.path.insert(0, "scripts/research")
from collections import Counter, defaultdict
from final_r12_common import *

def run(e):
    P = common.block(e, "provinces"); N = common.nodes(e)
    sc = defaultdict(int)
    for k, p in P.items():
        if isinstance(p, dict) and p.get("controller") and p.get("trade") and "trade_power" in p:
            sc[(p["trade"], p["controller"])] += m3(p["trade_power"])
    tot = bad = noentry = 0; diffs = []; seen = set()
    for n in N:
        for t, x in entries_of(n).items():
            if "province_power" not in x: continue
            seen.add((n["definitions"], t)); tot += 1
            d = m3(x["province_power"]) - sc.get((n["definitions"], t), 0)
            if d != 0: bad += 1; diffs.append(d)
    for key, v in sc.items():
        if key not in seen and v > 0 and key[1]: noentry += 1
    diffs.sort(key=abs)
    return tot, bad, noentry, diffs

by = defaultdict(lambda: [0, 0, 0, 0])
print("save  date  entries  mismatching  (no entry for a controlling tag)  median|d|  max|d|  (milli)")
for e in common.entries():
    if e["id"] in COPY_OF: continue
    tot, bad, noe, diffs = run(e)
    g = "bookmark 1444.11.11" if e["date"] == "1444.11.11" else ("start, later date, day 1" if e["kind"] == "start" and e["date"].endswith(".1.1") or (e["kind"] == "start" and e["date"].split(".")[2] == "1") else ("start, later date, day 11" if e["kind"] == "start" else "played/user"))
    by[g][0] += 1; by[g][1] += tot; by[g][2] += bad; by[g][3] += noe
    if e["kind"] != "start" or bad > 0 and False:
        med = abs(diffs[len(diffs) // 2]) if diffs else 0; mx = max((abs(x) for x in diffs), default=0)
        print(e["id"], e["date"], tot, bad, noe, med, mx)
print()
for g, (ns, tot, bad, noe) in by.items(): print(f"{g}: saves {ns}, entries {tot}, mismatching {bad} ({bad/tot:.4f}), controlling tags without entry {noe}")
