"""Independent check of the home-node bonus (R01 C-06) over all 85 saves: home md - top-province-node md vs 0.1 x steering merchants."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, ".")
import ver2_b_lib as L

TOL = 0.0015
rows = defaultdict(list)   # group -> list of (sid, tag, k, away, diff, embargo_touched)
for sid, s in L.saves():
    for tag, c in s["c"].items():
        home = L.home_node(s, tag)
        if home is None:
            continue
        ents = {nid: n["e"][tag] for nid, n in s["nodes"].items() if tag in n["e"]}
        k = sum(1 for e in ents.values() if e["trader"] and e["steer"])
        away = sum(1 for e in ents.values() if e["trader"] and e["collect"] and not e["cap"])
        tops = [nid for nid, n in s["nodes"].items() if n["top"] == tag and nid != home and tag in n["e"] and n["e"][tag]["md"] is not None and not (n["e"][tag]["trader"] and n["e"][tag]["collect"] and not n["e"][tag]["cap"])]
        if not tops or s["nodes"][home]["e"][tag]["md"] is None:
            continue
        mdH = s["nodes"][home]["e"][tag]["md"]
        mdT = [s["nodes"][nid]["e"][tag]["md"] for nid in tops]
        # embargo-affected if an embargoer of this country has own power at the home node or at any top node
        touched = any(L.own_power(s["nodes"][nid]["e"][t]) > 0 for nid in [home] + tops for t in c["emb_by"] if t in s["nodes"][nid]["e"])
        played = sid in ("S79", "S80", "U01", "U02", "U03", "U04", "U05")
        if k >= 1 and away == 0:
            grp = "steer>=1,no away"
        elif away >= 1:
            grp = "away collector"
        else:
            grp = "no steering, no away"
        diff = mdH - mdT[0]
        one = max(mdT) - min(mdT) <= TOL
        rows[(grp, "played" if played else "start", touched)].append((sid, tag, k, away, round(diff, 3), one))

for key in sorted(rows):
    r = rows[key]
    grp = key[0]
    if grp == "steer>=1,no away":
        ok = sum(1 for sid, tag, k, a, d, one in r if abs(d - 0.1 * k) <= TOL)
    else:
        ok = sum(1 for sid, tag, k, a, d, one in r if abs(d) <= TOL)
    print(f"{key}: n={len(r)} fits-prediction={ok}")
print()
NEW = ("U03", "U04", "U05")
for key in sorted(rows):
    if key[1] == "played":
        tagsaves = defaultdict(list)
        for sid, tag, k, a, d, one in rows[key]:
            tagsaves[tag].append((sid, k, d))
        print(key, {t: [(x[0], x[1], x[2]) for x in v if x[0] in NEW] for t, v in sorted(tagsaves.items()) if any(x[0] in NEW for x in v)})

print()
start = rows[("steer>=1,no away", "start", False)]
print("start snapshots, steer>=1 & no away, not embargo-touched: n=%d, |home-top|<=%.4f: %d" % (len(start), TOL, sum(1 for r in start if abs(r[4]) <= TOL)))
print("  other diffs:", sorted(Counter(round(r[4], 2) for r in start if abs(r[4]) > TOL).items())[:10])
