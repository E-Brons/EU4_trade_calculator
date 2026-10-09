import sys
sys.path.insert(0, "scripts/research")
import u06_load as L
def f(x, d=None):
    try: return float(x)
    except (TypeError, ValueError): return d
order = ["S79","S80","U03","U04","U05","U06"]
rows = {}
for s in order:
    for n in L.nodes(s):
        e = n.get("TUR")
        if not isinstance(e, dict): continue
        act = "collect" if "total" in e else ("steer" if "type" in e else ("merchant" if e.get("has_trader") else "-"))
        rows[(s, n["definitions"])] = dict(act=act, cap=bool(e.get("has_capital")), md=f(e.get("max_demand")), pp=f(e.get("province_power"), 0), sp=f(e.get("ship_power"), 0),
            prev=f(e.get("prev"), 0), mp=f(e.get("max_pow")), val=f(e.get("val")), tot=f(e.get("total")), money=f(e.get("money")))
nodes = sorted({k[1] for k in rows})
print("node | " + " | ".join(order))
for nd in nodes:
    cells = []
    for s in order:
        r = rows.get((s, nd))
        if not r: cells.append("-"); continue
        X = round(r["money"] / r["tot"] - 1, 3) if r["tot"] and r["money"] is not None else None
        cells.append(f"{r['act'][:2]}{'*' if r['cap'] else ''} md={r['md']} mp={r['mp']} X={X}")
    if any(rows.get((s, nd), {}).get("act") in ("collect", "steer") or rows.get((s, nd), {}).get("sp") for s in order):
        print(nd, "|", " | ".join(cells))
