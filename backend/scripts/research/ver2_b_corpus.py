"""Independent re-test over all 85 saves: away factor 0.5, max_demand constancy, has_capital == trade_port node."""
import statistics
import sys
from collections import Counter
sys.path.insert(0, ".")
import ver2_b_lib as L

TOL = 0.0015
NEW = ("U03", "U04", "U05")
away_hit = Counter(); away_miss = []; away_nobase = Counter()
const = Counter(); multi = []
cap_eq = Counter(); cap_bad = []
for sid, s in L.saves():
    grp = "new" if sid in NEW else "old"
    # ---- away factor
    for tag, c in s["c"].items():
        home = L.home_node(s, tag)
        ents = {nid: n["e"][tag] for nid, n in s["nodes"].items() if tag in n["e"] and n["e"][tag]["md"] is not None}
        def clean(nid):  # no embargoer of this country has own power at the node
            return all(L.own_power(s["nodes"][nid]["e"][t]) <= 0 for t in c["emb_by"] if t in s["nodes"][nid]["e"])
        def cls(nid):
            return "dom" if nid == home or s["nodes"][nid]["top"] == tag else "for"
        base = {"dom": [], "for": []}
        for nid, e in ents.items():
            if not e["trader"] and not e["collect"] and not e["steer"] and clean(nid):
                base[cls(nid)].append(e["md"])
        for nid, e in ents.items():
            if e["trader"] and e["collect"] and not e["cap"]:
                if not clean(nid):
                    away_nobase[(grp, "embargoer power at the node")] += 1
                    continue
                b = base[cls(nid)]
                if not b or max(b) - min(b) > TOL:
                    away_nobase[(grp, "no single baseline")] += 1
                    continue
                if abs(e["md"] - 0.5 * b[0]) <= TOL:
                    away_hit[grp] += 1
                else:
                    away_miss.append((sid, tag, nid, e["md"], b[0], round(e["md"] / b[0], 4)))
        # ---- constancy (non-embargoed country, has a home md, >=1 foreign node)
        if home is not None and not c["emb_by"]:
            vals = {round(e["md"], 3) for nid, e in ents.items() if nid != home and s["nodes"][nid]["top"] != tag and not (e["trader"] and e["collect"] and not e["cap"])}
            if vals:
                const[(grp, len(vals) == 1)] += 1
                if len(vals) > 1:
                    multi.append((sid, tag, sorted(vals)[:4], len(vals)))
        # ---- has_capital node == trade_port node
        port = c["port"]
        if port is not None:
            pn = L.PROV2NODE.get(int(port))
            if home is None:
                cap_eq[(grp, "no has_capital entry")] += 1
            elif pn == home:
                cap_eq[(grp, "has_capital node == node of trade_port")] += 1
            else:
                cap_eq[(grp, "DIFFERENT")] += 1
                cap_bad.append((sid, tag, home, pn))

print("away factor (clean away entries with a single same-class baseline): hits", dict(away_hit), "misses", len(away_miss))
for m in away_miss[:12]: print("   miss", m)
print("   not testable:", dict(away_nobase))
print("constancy (non-embargoed country-saves with a home md and >=1 foreign node): ", dict(const))
for m in multi[:8]: print("   multi", m)
print("has_capital node vs node of trade_port:", dict(cap_eq), "different examples", cap_bad[:5])
