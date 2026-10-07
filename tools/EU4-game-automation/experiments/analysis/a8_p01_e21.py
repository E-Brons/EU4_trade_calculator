"""P01 ragusa weights/links; E21 Naxos aggregates after losing its last province."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); from common import block, save, nodes, node_list, m3, as_list, ROOT, OUT
TN = json.load(open(ROOT / "backend/data/tradenodes.json"))["nodes"]
def links(p, src):
    order = [n["definitions"] for n in node_list(p)]; res = {}
    for n in node_list(p):
        for i in as_list(n.get("incoming")):
            if isinstance(i, dict) and order[int(i["from"]) - 1] == src:
                res[n["definitions"]] = (i.get("value"), i.get("add"))
    return res
print("ragusa outgoing:", [o["target"] for o in TN["ragusa"]["outgoing"]])
for e in ["E01c", "P01"]:
    for w in ("t1", "t2"):
        p = save(e, w); n = nodes(p)["ragusa"]
        st = {t: (v.get("type"), v.get("steer_power"), v.get("val")) for t, v in n.items() if isinstance(v, dict) and v.get("type")}
        print(f"  {e} {w} weights {n.get('steer_power')} outgoing {n.get('outgoing')} links {links(p, 'ragusa')} steerers {st}")
print("E21 Naxos (NAX) at its nodes; base vs d_1444.12.03 / d_1444.12.15 / t1:")
for f in ["E00/base_1444.12.01.eu4", "E21/d_1444.12.03.eu4", "E21/d_1444.12.15.eu4", "E21/t1_1445.01.01.eu4", "E01d/t1_1445.01.01.eu4"]:
    p = OUT / f; c = block(p, "countries").get("NAX", {})
    rows = []
    for nid, n in nodes(p).items():
        x = n.get("NAX"); tp = dict(zip(as_list(n.get("top_power")), as_list(n.get("top_power_values"))))
        if isinstance(x, dict) or "NAX" in tp:
            rows.append((nid, {k: x.get(k) for k in ("val", "max_pow", "province_power", "total", "has_capital")} if isinstance(x, dict) else None, tp.get("NAX"),
                         n.get("retain_power"), n.get("pull_power")))
    print(f"  {f}: NAX num_of_cities={c.get('num_of_cities')} capital={c.get('capital')}")
    for r in rows[:6]: print("     ", r)
