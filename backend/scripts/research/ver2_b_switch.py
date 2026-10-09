"""Independent within-country switch test for the away factor: nodes where a country starts/stops collecting away between two saves of the same campaign."""
import statistics
import sys
sys.path.insert(0, ".")
import ver2_b_lib as L

PAIRS = [("S79", "S80"), ("S80", "U03"), ("U03", "U04"), ("U04", "U05")]
data = dict(L.saves({"S79", "S80", "U03", "U04", "U05"}))


def away(e):
    return e["trader"] and e["collect"] and not e["cap"]


def kind(e):
    return "away" if away(e) else "steer" if e["steer"] else "passive" if not e["trader"] else "other"


rows = []
for a, b in PAIRS:
    A, B = data[a], data[b]
    for tag in A["c"]:
        if tag not in B["c"]:
            continue
        ctrl = []
        sw = []
        for nid, nb in B["nodes"].items():
            ea, eb = A["nodes"].get(nid, {"e": {}})["e"].get(tag), nb["e"].get(tag)
            if not ea or not eb or ea["md"] is None or eb["md"] is None:
                continue
            if away(ea) != away(eb):
                sw.append((nid, kind(ea), kind(eb), ea["md"], eb["md"]))
            elif not away(ea) and not ea["cap"] and not eb["cap"]:
                ctrl.append(eb["md"] / ea["md"])
        if sw and len(ctrl) >= 5:
            med = statistics.median(ctrl)
            tight = sum(1 for c in ctrl if abs(c - med) <= 0.005) / len(ctrl)
            for nid, ka, kb, ma, mb in sw:
                r = (mb / ma) / med
                rows.append((a, b, tag, nid, f"{ka}->{kb}", ma, mb, round(med, 4), round(tight, 2), round(r, 4)))
print("pair tag node change md_A md_B control-median control-tightness normalized-ratio(=md_B/md_A / control)")
for r in rows:
    print("  ", r)
to_away = [r[-1] for r in rows if r[4].endswith("away")]
from_away = [r[-1] for r in rows if r[4].startswith("away")]
print("entering away: n=%d normalized ratios %s" % (len(to_away), sorted(to_away)))
print("leaving away:  n=%d normalized ratios %s" % (len(from_away), sorted(from_away)))
print("first steer->away switches:", [(r[0], r[1], r[2], r[3]) for r in rows if r[4] == "steer->away"])
