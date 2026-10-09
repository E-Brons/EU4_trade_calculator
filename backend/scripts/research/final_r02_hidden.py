"""R02 final, test 3: the merchant without `total` that IS halved (S79/U02 english_channel POR) and the collector count.
(a) node field num_collectors == number of entries with `total` or `has_capital` (PIR excluded)?  exceptions listed
(b) merchant-only entries (has_trader, no type/total/has_capital) whose power share val_eff/collector_power is < 0.001
    (a share that truncates to 0.000 in the 3-decimal fixed point): are they halved?  compared with the baseline of test 1
(c) smallest `total` and `power_fraction` keys in the corpus (are zero values ever written?)
Usage: .venv/bin/python scripts/research/final_r02_hidden.py"""
import statistics
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import common
import final_r02_lib as L

c = Counter()
bad = []
cands = []
mn_total = mn_pf = 1e9
for e in common.entries():
    s = L.load(e)
    base = defaultdict(list)
    def kl(nid, tag):
        return "dom" if (s["nodes"][nid]["top"] == tag or nid == L.port_node(s, tag)) else "for"
    for nid, n in s["nodes"].items():
        for tag, x in n["e"].items():
            if not (x["trader"] or x["steer"] or x["coll"] or x["cap"]) and x["md"] is not None and not L.embargo_active(s, nid, tag):
                base[(tag, kl(nid, tag))].append(x["md"])
    for n in common.nodes(e):
        nid = n["definitions"]
        ents = s["nodes"][nid]["e"]
        nc = n.get("num_collectors")
        if nc is not None:
            k = sum(1 for t, x in ents.items() if (x["coll"] or x["cap"]) and t != "PIR")
            c["nodes with num_collectors"] += 1
            if int(nc) == k:
                c["num_collectors == keyed collectors"] += 1
            else:
                bad.append((e["id"], nid, int(nc), k))
        cp = n.get("collector_power")
        for tag, x in ents.items():
            if x["coll"]:
                raw = n[tag]
                mn_total = min(mn_total, float(raw["total"]))
                if "power_fraction" in raw:
                    mn_pf = min(mn_pf, float(raw["power_fraction"]))
                if float(raw.get("power_fraction", 1)) == 0 or float(raw["total"]) == 0:
                    c["collector with a zero total/power_fraction written"] += 1
            if cp is not None and float(cp) > 0 and x["trader"] and not (x["steer"] or x["coll"] or x["cap"]) and x["val"]:
                frac = ((x["val"] - x["tout"] + x["tin"])) / float(cp)
                if frac < 0.001:
                    b = base.get((tag, kl(nid, tag)))
                    r = x["md"] / statistics.median(b) if b else None
                    cands.append((e["id"], nid, tag, round(frac, 5), x["md"], None if r is None else round(r, 4)))
print("(a)", dict(c))
print("    exceptions (save, node, num_collectors, keyed collectors):", bad)
print("(b) merchant-only entries with a power share < 0.001 of collector_power:", len(cands))
for x in cands:
    print("    ", x)
print("(c) smallest `total` key:", mn_total, " smallest `power_fraction` key:", mn_pf)
