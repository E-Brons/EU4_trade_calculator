"""Countries whose adm AND dip tech both rose by 1 between two consecutive saves: dX and what else changed (modifier names, ideas, policies, reforms)."""
import sys
from collections import defaultdict
sys.path.insert(0, "scripts/research")
import u06_load as L
from u06_dx_tech import entries
from app.parsing.clausewitz import as_list
a, b = sys.argv[1], sys.argv[2]
ca, cb = L.block(a, "countries"), L.block(b, "countries")
EA, EB = entries(a), entries(b)
def names(c, key, sub):
    return sorted({m.get(sub) for m in as_list(c.get(key)) if isinstance(m, dict)})
def reforms(c):
    g = c.get("government")
    return sorted((g or {}).get("reform_stack", {}).get("reforms", [])) if isinstance(g, dict) else []
rows = defaultdict(list)
for (nd, tag), xa in EA.items():
    if (nd, tag) not in EB or xa[1:] != EB[(nd, tag)][1:]: continue
    A, B = ca.get(tag), cb.get(tag)
    if not (isinstance(A, dict) and isinstance(B, dict)): continue
    ta, tb = A.get("technology") or {}, B.get("technology") or {}
    if tb.get("adm_tech", 0) - ta.get("adm_tech", 0) != 1 or tb.get("dip_tech", 0) - ta.get("dip_tech", 0) != 1: continue
    rows[tag].append((nd, round(EB[(nd, tag)][0] - xa[0], 2)))
print(f"{a}->{b}: adm+1 and dip+1 (mil any): countries with comparable collecting entries: {len(rows)}")
for tag, lst in sorted(rows.items()):
    A, B = ca[tag], cb[tag]
    dm = (sorted(set(names(B, 'modifier', 'modifier')) - set(names(A, 'modifier', 'modifier'))), sorted(set(names(A, 'modifier', 'modifier')) - set(names(B, 'modifier', 'modifier'))))
    di = A.get("active_idea_groups") != B.get("active_idea_groups")
    dp = names(A, "active_policy", "policy") != names(B, "active_policy", "policy")
    dr = reforms(A) != reforms(B)
    par = lambda c: ((c.get("parliament") or {}).get("enacted_parliament_issue"), ((c.get("parliament") or {}).get("active_parliament_issue") or {}).get("which") if isinstance((c.get("parliament") or {}).get("active_parliament_issue"), dict) else None)
    print(tag, "dX per node:", sorted({d for _, d in lst}), "n", len(lst), "| tech", (ta := A["technology"])["dip_tech"], "->", B["technology"]["dip_tech"], "| mods+/-", dm, "| ideas chg", di, "| policy chg", dp, "| reform chg", dr, "| parliament", par(A), "->", par(B))
