"""R02 final, test 7 (interaction with R01): home-node bonus and the away collector.
For each country-save with (i) a has_capital entry H at the node of trade_port, (ii) a node D where the country is the top
province owner (top_provinces[0] == tag), D != home, the country has no merchant there and no embargoer with power at D or at home:
   diff = md(H) - md(D).  k = number of steering merchants of the country (entries with key `type`), away = number of away collectors.
Hypothesis under test (wiki): diff = 0.1 * k when away == 0; diff = 0 when away >= 1.  Usage: .venv/bin/python scripts/research/final_r02_homebonus.py"""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r02_lib as L

tab = defaultdict(Counter)
rows = []
for sid, s in L.all_saves():
    per = defaultdict(lambda: {"k": 0, "away": 0, "home": None, "D": []})
    for nid, n in s["nodes"].items():
        pn_cache = {}
        for tag, e in n["e"].items():
            if tag == "PIR":
                continue
            p = per[tag]
            if e["steer"] and not e["cap"]:
                p["k"] += 1
            if L.is_away(e):
                p["away"] += 1
            if e["cap"] and e["md"] is not None and nid == L.port_node(s, tag) and not L.embargo_active(s, nid, tag):
                p["home"] = (nid, e["md"])
            if n["top"] == tag and nid != L.port_node(s, tag) and not (e["trader"] or e["steer"] or e["coll"] or e["cap"]) \
                    and e["md"] is not None and not L.embargo_active(s, nid, tag):
                p["D"].append((nid, e["md"]))
    for tag, p in per.items():
        if p["home"] is None or len(p["D"]) == 0:
            continue
        dvals = {round(x[1], 3) for x in p["D"]}
        if len(dvals) != 1:
            continue
        diff = p["home"][1] - next(iter(dvals))
        k, aw = p["k"], p["away"]
        exp = 0.1 * k if aw == 0 else 0.0
        if abs(diff) <= 0.0015 and exp == 0:
            res = "home == domestic reference, expected 0 (k=%d, away=%d)" % (k, aw) if False else "no bonus, expected none"
        else:
            res = "bonus matches 0.1*k" if abs(diff - exp) <= 0.0015 and exp > 0 else ("MISMATCH")
        campaign = sid in ("S79", "S80", "U01", "U02", "U03", "U04", "U05", "U06")
        key = ("campaign saves S79..U06" if campaign else "start snapshots S01-S78", "away>=1" if aw else "no away", "k=0" if k == 0 else "k>=1")
        tab[key][res] += 1
        if campaign and k >= 1:
            rows.append((sid, tag, "k=%d away=%d" % (k, aw), "home md", p["home"][1], "ref md", sorted(dvals)[0], "diff", round(diff, 3), "expected", round(exp, 3)))
for key, cnt in sorted(tab.items()):
    print(key, dict(cnt))
print("country-saves of the campaign saves with k >= 1 (sid, tag, k/away, home md, reference md, diff, expected):")
for r in rows:
    print("  ", r)
