import sys
sys.path.insert(0, "scripts/research")
import common
from collections import Counter
from app.parsing.tradenodes import load_trade_graph
G = load_trade_graph()
ends = [n for n in G.nodes if not G.outgoing(n)]
print("end nodes", ends)
def f(x):
    try: return float(x)
    except Exception: return 0.0
c = Counter(); rows = []
for e in common.entries():
    if e["id"] in ("U01", "U02"): continue
    for n in common.nodes(e):
        if n["definitions"] not in ends: continue
        allsum = colsum = 0.0; non = []
        for t, d in n.items():
            if isinstance(d, dict) and len(t) <= 4 and t.upper() == t and set(d) - {"max_demand"}:
                eff = f(d.get("val")) - f(d.get("t_out")) + f(d.get("t_in"))
                allsum += eff
                if "total" in d or d.get("has_capital"): colsum += eff
                else: non.append((t, round(eff, 3), "has_trader" in d, "type" in d))
        rec = f(n.get("retain_power"))
        c["nodes"] += 1
        c["retain==collectors"] += abs(colsum - rec) <= 0.0105
        c["retain==all entries"] += abs(allsum - rec) <= 0.0105
        c["nodes with non-collecting entries"] += bool(non)
        if abs(colsum - rec) > 0.0105: rows.append((e["id"], n["definitions"], round(colsum, 3), round(allsum, 3), rec, non, n.get("num_collectors")))
        c["pull_power present"] += n.get("pull_power") is not None
print(dict(c))
for r in rows: print(r)
