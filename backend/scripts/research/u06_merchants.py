"""Merchant count (len(countries.<TAG>.merchants.envoy)) vs dip tech level: TUR series and dip-step cases over consecutive saves."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import u06_load as L
from app.parsing.clausewitz import as_list
order = ["S79","S80","U03","U04","U05","U06"]
def nmerch(c):
    m = c.get("merchants")
    return len(as_list(m.get("envoy"))) if isinstance(m, dict) else 0
print("TUR:", [(s, L.tur(s)["technology"]["dip_tech"], nmerch(L.tur(s))) for s in order])
cs = {s: L.block(s, "countries") for s in order}
by = defaultdict(Counter); allp = defaultdict(Counter)
for a, b in zip(order, order[1:]):
    for tag, ca in cs[a].items():
        cb = cs[b].get(tag)
        if not (isinstance(ca, dict) and isinstance(cb, dict) and "technology" in ca and "technology" in cb): continue
        ta, tb = ca["technology"], cb["technology"]
        dm = nmerch(cb) - nmerch(ca)
        ddip, dadm = tb["dip_tech"] - ta["dip_tech"], tb["adm_tech"] - ta["adm_tech"]
        ia, ib = ca.get("active_idea_groups") or {}, cb.get("active_idea_groups") or {}
        same_ideas = ia == ib
        if ddip == 1 and dadm == 0 and same_ideas: by[(ta["dip_tech"], tb["dip_tech"])][dm] += 1
        if ddip == 0 and dadm == 1 and same_ideas: allp[("adm", ta["adm_tech"], tb["adm_tech"])][dm] += 1
        if ddip == 1 and dadm == 1 and same_ideas: allp[("adm+dip", ta["dip_tech"], tb["dip_tech"])][dm] += 1
print("dip +1 step (adm, ideas unchanged): d(merchants) by level step")
for k in sorted(by): print(" ", k, dict(by[k]))
print("other steps:")
for k in sorted(allp): print(" ", k, dict(allp[k]))
