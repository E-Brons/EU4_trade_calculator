import sys
sys.path.insert(0, "scripts/research")
import u06_load as L
from app.parsing.clausewitz import as_list
def f(x, d=0.0):
    try: return float(x)
    except (TypeError, ValueError): return d
for s in ("U05", "U06"):
    t = L.tur(s)
    emb = as_list(t.get("trade_embargoed_by"))
    print(s, "TUR trade_embargoed_by:", emb)
    nd = {n["definitions"]: n for n in L.nodes(s)}
    for node in ("philippines", "hormuz", "constantinople", "basra", "aleppo", "alexandria", "malacca", "crimea", "genua"):
        own = {e: round(f(nd[node][e].get("max_pow")) - f(nd[node][e].get("prev")), 1) for e in emb if isinstance(nd[node].get(e), dict) and f(nd[node][e].get("max_pow")) - f(nd[node][e].get("prev")) > 0.05}
        print("   ", node.ljust(15), "md", nd[node]["TUR"]["max_demand"], "embargoers with own power:", own)
