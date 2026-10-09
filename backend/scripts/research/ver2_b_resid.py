"""Independent check of the R06 merchant term R = 2 + 5a + 15b (counts per save) and of the TUR / MKL / SND details."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, ".")
import ver2_b_lib as L

TOL = 0.0025
REFORMS = {"mercantilistic_approach_reform", "pious_merchants_reform"}
PLAYED = ("S79", "S80", "U01", "U02", "U03", "U04", "U05")
summary = {}
details = defaultdict(list)
for sid, s in L.saves():
    merch = {}      # tag -> list of (node, res)
    nontrader_bad = []
    snap_bad = 0
    for nid, n in s["nodes"].items():
        for tag, e in n["e"].items():
            if e["mp"] is None:
                continue
            res = e["mp"] - e["pp"] - e["sp"] - e["prev"] - 5 * e["cap"] - sum(p for _, p in e["mods"])
            if e["trader"]:
                merch.setdefault(tag, []).append((nid, round(res, 3)))
            elif abs(res) > TOL:
                nontrader_bad.append((tag, nid, round(res, 3)))
    fit = 0
    fails = []
    for tag, lst in merch.items():
        c = s["c"].get(tag)
        if not c:
            fails.append((tag, "no country block"))
            continue
        R = 2 + 5 * bool(c["reforms"] & REFORMS) + 15 * (c["ideas"].get("trade_ideas", 0) >= 5)
        vals = sorted({v for _, v in lst})
        if all(abs(v - R) <= TOL for _, v in lst):
            fit += 1
        else:
            fails.append((tag, vals, R))
            details[sid].append((tag, lst, R))
    summary[sid] = (len(merch), fit, fails, nontrader_bad)

print("save: merchant countries / fit / failures / entries without has_trader with residual != 0")
tot_nt = 0
for sid, (n, fit, fails, nt) in summary.items():
    if sid in PLAYED:
        print(f"  {sid}: {n} / {fit} / {fails} / {nt}")
    else:
        tot_nt += len(nt)
        if n and (fit != n or nt):
            print(f"  {sid} (snapshot): merchant countries {n}, fit {fit}, nontrader residual entries {len(nt)}")
snap_merchants = sum(v[0] for k, v in summary.items() if k not in PLAYED)
snap_fit = sum(v[1] for k, v in summary.items() if k not in PLAYED)
print(f"snapshots S01-S78: merchant countries {snap_merchants}, formula-R fit {snap_fit}; entries without merchant and residual != 0: {tot_nt}")
# snapshots: is residual (for merchant entries) zero?
zero = nonzero = 0
for sid, s in L.saves():
    if sid in PLAYED:
        continue
    for nid, n in s["nodes"].items():
        for tag, e in n["e"].items():
            if e["mp"] is None or not e["trader"]:
                continue
            res = e["mp"] - e["pp"] - e["sp"] - e["prev"] - 5 * e["cap"] - sum(p for _, p in e["mods"])
            if abs(res) <= TOL: zero += 1
            else: nonzero += 1
print(f"snapshots: merchant entries with residual 0: {zero}, != 0: {nonzero}")
print()
for sid in ("U03", "U04", "U05"):
    for tag, lst, R in details[sid]:
        print(sid, tag, "formula R", R, "entries:", lst[:8])
print()
# TUR
for sid in PLAYED:
    s = dict(L.saves({sid}))[sid]
    tur = [(nid, round(n["e"]["TUR"]["mp"] - n["e"]["TUR"]["pp"] - n["e"]["TUR"]["sp"] - n["e"]["TUR"]["prev"] - 5 * n["e"]["TUR"]["cap"] - sum(p for _, p in n["e"]["TUR"]["mods"]), 3)) for nid, n in s["nodes"].items() if "TUR" in n["e"] and n["e"]["TUR"]["trader"] and n["e"]["TUR"]["mp"] is not None]
    print(sid, "TUR merchant-entry residuals:", Counter(v for _, v in tur), "home extras:", {nid: round(n["e"]["TUR"]["mp"] - n["e"]["TUR"]["pp"] - n["e"]["TUR"]["sp"] - n["e"]["TUR"]["prev"], 3) for nid, n in s["nodes"].items() if "TUR" in n["e"] and n["e"]["TUR"]["cap"]})
