import sys
sys.path.insert(0, "scripts/research")
import u06_load as L
from app.parsing.clausewitz import as_list
def f(x, d=0.0):
    try: return float(x)
    except (TypeError, ValueError): return d
order = ["U03","U04","U05","U06"]
for s in order:
    tot_money = 0.0; coll = []; Rs = []; merch_nodes = []
    for n in L.nodes(s):
        e = n.get("TUR")
        if not isinstance(e, dict): continue
        if e.get("has_trader"): merch_nodes.append(n["definitions"] + ("*" if "total" in e else "s" if "type" in e else "?"))
        if "total" in e:
            tot_money += f(e.get("money")); coll.append((n["definitions"], round(f(e.get("money")), 3), round(f(e.get("total")), 3)))
        if e.get("has_trader") or "total" in e or "type" in e:
            mods = sum(f(m.get("power")) for m in as_list(e.get("modifier")) if isinstance(m, dict))
            R = f(e.get("max_pow")) - f(e.get("province_power")) - f(e.get("ship_power")) - f(e.get("prev")) - 5 * bool(e.get("has_capital")) - mods
            Rs.append((n["definitions"], round(R, 2)))
    print(s, "TUR trade income (sum money of collecting entries):", round(tot_money, 3), "| n merchants placed:", len(merch_nodes))
    print("   collecting (node, money, total):", coll)
    print("   merchant nodes:", merch_nodes)
    print("   extras R at merchant entries:", sorted(set(r for _, r in Rs)), [x for x in Rs if x[1] != 17.0][:5])
