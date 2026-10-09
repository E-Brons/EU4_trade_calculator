"""R02 final, test 1: max_demand of away-collecting entries (key `total`, no `has_capital`) against the same country's
max_demand at passive, merchant-free, embargo-clean nodes of the same class (domestic: top_provinces[0] == tag or node of
trade_port; foreign otherwise). Independent code: raw save keys only.
Prints counts, every exception, and the ratio distribution. Usage (from backend/): .venv/bin/python scripts/research/final_r02_away.py"""
import statistics
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r02_lib as L

TOL = 0.0011      # |md - 0.5*base| <= TOL : md is rounded to 3 decimals (+-0.0005), base too (0.5*+-0.0005)
SPREAD = 0.0015   # passive baselines of one class must agree within this


def klass(s, nid, tag):
    return "dom" if (s["nodes"][nid]["top"] == tag or nid == L.port_node(s, tag)) else "for"


def passive(e):
    return not (e["trader"] or e["steer"] or e["coll"] or e["cap"]) and e["md"] is not None


summary = Counter()
rows = []
no_base = []
by_save = Counter()
for sid, s in L.all_saves():
    base = defaultdict(list)    # tier 1: passive, merchant-free entries
    base2 = defaultdict(list)   # tier 2 (used only when tier 1 is empty): adds the home entry (has_capital, collecting at home)
    for nid, n in s["nodes"].items():
        for tag, e in n["e"].items():
            if L.embargo_active(s, nid, tag) or e["md"] is None:
                continue
            if passive(e):
                base[(tag, klass(s, nid, tag))].append(e["md"])
                base2[(tag, klass(s, nid, tag))].append(e["md"])
            elif e["cap"] and e["coll"]:
                base2[(tag, klass(s, nid, tag))].append(e["md"])
    for nid, n in s["nodes"].items():
        for tag, e in n["e"].items():
            if not L.is_away(e):
                continue
            summary["away entries (all 86 manifest entries)"] += 1
            by_save[sid] += 1
            if not e["trader"]:
                summary["away without has_trader"] += 1
            emb = L.embargo_active(s, nid, tag)
            k = klass(s, nid, tag)
            b = base.get((tag, k), [])
            tier = 1
            if not b:
                b = base2.get((tag, k), [])
                tier = 2
            if not b:
                no_base.append((sid, nid, tag, k, e["md"], "embargo-active" if emb else "clean"))
                summary["no baseline (" + ("embargo-active" if emb else "clean") + ")"] += 1
                continue
            bm = statistics.median(b)
            spread = max(b) - min(b)
            ratio = e["md"] / bm
            rows.append((sid, nid, tag, k, e["md"], bm, len(b), spread, ratio, emb, tier))
print("manifest entries", len(L.all_saves()), "| away entries per save:", dict(sorted(by_save.items())))
for k, v in sorted(summary.items()):
    print(f"  {k}: {v}")
print("\nno-baseline entries:")
for r in no_base:
    print("  ", r)

def dedup(rs):
    """U01/U02 are copies of S80/S79: count the distinct ones only."""
    return [r for r in rs if r[0] not in ("U01", "U02")]

for label, sel in (("CLEAN (no embargoer with own power at the node)", lambda r: not r[9]),
                   ("EMBARGO-ACTIVE (some embargoer has own power)", lambda r: r[9])):
    rs = [r for r in rows if sel(r)]
    d = dedup(rs)
    ok = [r for r in rs if abs(r[4] - 0.5 * r[5]) <= TOL and r[7] <= SPREAD]
    okd = [r for r in d if abs(r[4] - 0.5 * r[5]) <= TOL and r[7] <= SPREAD]
    print(f"\n{label}: {len(rs)} entries with a baseline (distinct saves: {len(d)})")
    print(f"  md == 0.5 x baseline within {TOL}: {len(ok)} (distinct: {len(okd)})")
    print("  max |md - 0.5 x baseline| among the matching entries:", round(max((abs(r[4] - 0.5 * r[5]) for r in ok), default=0), 5))
    bad = [r for r in rs if r not in ok]
    for r in bad:
        print("   NOT 0.5:", "save=%s node=%s tag=%s class=%s md=%.3f base=%.3f (n=%d spread=%.4f) ratio=%.4f" % r[:9])
    qs = sorted(r[8] for r in rs)
    print("  ratio min/median/max:", round(qs[0], 4), round(statistics.median(qs), 4), round(qs[-1], 4))
    print("  ratio < 0.4985:", sum(1 for q in qs if q < 0.4985), "  in [0.4985,0.5015]:", sum(1 for q in qs if 0.4985 <= q <= 0.5015), "  > 0.5015:", sum(1 for q in qs if q > 0.5015))
    sp = [r[7] for r in rs]
    print("  baseline tier 1 (passive):", sum(1 for r in rs if r[10] == 1), " tier 2 (passive + home entry):", sum(1 for r in rs if r[10] == 2))
    print("  baseline spread > %s (ambiguous baselines):" % SPREAD, sum(1 for x in sp if x > SPREAD))
