import sys, json
sys.path.insert(0, "scripts/research")
import u06_load as L
from app.parsing.clausewitz import as_list
order = ["S79","S80","U03","U04","U05","U06"]
def mods(t):
    out = {}
    for m in as_list(t.get("modifier")):
        if isinstance(m, dict): out[m.get("modifier")] = m.get("date")
    return out
prev = None
for s in order:
    t = L.tur(s)
    m = mods(t)
    pol = t.get("active_policy")
    par = t.get("parliament")
    est = []
    for e in as_list(t.get("estate")):
        if isinstance(e, dict):
            est.append((e.get("type"), e.get("loyalty"), [p[0] if isinstance(p, list) else p for p in as_list(e.get("granted_privileges"))]))
    print("=====", s, L.meta_date(s))
    print(" modifiers:", sorted(m))
    print(" active_policy:", json.dumps(pol, default=str)[:300])
    print(" parliament enacted/active:", par.get("enacted_parliament_issue") if isinstance(par, dict) else par, "|", json.dumps((par or {}).get("active_parliament_issue"), default=str)[:200] if isinstance(par, dict) else "")
    for n, loy, pr in est:
        print("  estate", n, "loyalty", loy, "privs", pr)
    if prev is not None:
        print(" CHANGED modifiers +", sorted(set(m) - set(prev[0])), "-", sorted(set(prev[0]) - set(m)))
    prev = (m,)
