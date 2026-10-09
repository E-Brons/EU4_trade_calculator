import sys
sys.path.insert(0, "scripts/research")
import common
from collections import defaultdict
ents = {e["id"]: e for e in common.entries()}
def f(x):
    try: return float(x)
    except Exception: return 0.0
# distinct-save counts (U01=S80, U02=S79 are copies)
distinct = [i for i in ents if i not in ("U01", "U02")]
pn = 0
for i in distinct:
    pn += sum(1 for n in common.nodes(ents[i]) if n.get("pull_power") is not None)
print("distinct saves", len(distinct), "pull nodes in distinct saves", pn)
# retain mismatches (collect = total key or has_capital)
import itertools
for sid in ("U05", "U04"):
    for n in common.nodes(ents[sid]):
        if n["definitions"] in ("ethiopia", "gulf_of_aden"):
            print("==", sid, n["definitions"], "retain", n.get("retain_power"), "pull", n.get("pull_power"), "total", n.get("total"), "p_pow", n.get("p_pow"))
            s = 0.0; sp = 0.0; coll = 0.0
            for tag, c in n.items():
                if isinstance(c, dict) and len(tag) <= 4 and tag.upper() == tag and set(c) - {"max_demand"}:
                    eff = f(c.get("val")) - f(c.get("t_out")) + f(c.get("t_in"))
                    if tag == "AFA" or "total" in c and False: print("  ", tag, sorted(set(c)), "eff", round(eff, 3))
            if "AFA" in n: print("   AFA entry", {k: n["AFA"][k] for k in n["AFA"] if k in ("val","max_pow","province_power","prev","ship_power","type","total","has_trader","has_capital")})
            else: print("   no AFA entry")
