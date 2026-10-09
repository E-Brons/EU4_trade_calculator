import sys, json
sys.path.insert(0, "scripts/research")
import u06_load as L
from app.parsing.clausewitz import as_list
order = ["S79","S80","U03","U04","U05","U06"]
def pol(t): return sorted(p["policy"] for p in as_list(t.get("active_policy")) if isinstance(p, dict))
def par(t):
    p = t.get("parliament") or {}
    a = p.get("active_parliament_issue")
    return (p.get("enacted_parliament_issue"), a.get("which") if isinstance(a, dict) else None, a.get("date") if isinstance(a, dict) else None)
def flags(t):
    f = t.get("flags") or {}
    return sorted(f) if isinstance(f, dict) else f
def var(t): return {k: v for k, v in (t.get("variables") or {}).items()}
prev = None
for s in order:
    t = L.tur(s)
    cur = dict(tech=t["technology"], pol=pol(t), par=par(t), flags=flags(t), var=var(t), hidden=sorted((t.get("hidden_flags") or {})))
    print("==", s)
    if prev:
        for k in cur:
            if cur[k] != prev[k]:
                if k in ("pol", "flags", "hidden"):
                    print("  ", k, "+", sorted(set(map(str, cur[k])) - set(map(str, prev[k]))), "-", sorted(set(map(str, prev[k])) - set(map(str, cur[k]))))
                elif k == "var":
                    d = {kk: (prev[k].get(kk), cur[k].get(kk)) for kk in set(cur[k]) | set(prev[k]) if cur[k].get(kk) != prev[k].get(kk)}
                    print("   var changes:", json.dumps(d, default=str)[:400])
                else:
                    print("  ", k, prev[k], "->", cur[k])
    prev = cur
