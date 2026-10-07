"""E06 efficiency, E02 ruler skill, P02 hangzhou, P06 california, P03/P04 home bonus, E21-ready check."""
import re, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); from common import block, save, nodes, m3, as_list, text, ROOT
TN = json.load(open(ROOT / "backend/data/tradenodes.json"))["nodes"]
def ent(e, w, node, tag): return nodes(save(e, w))[node].get(tag, {})
print("E06 venice VEN money/total (efficiency ratio):")
for e in ["E01a", "E01b", "E01c", "E01d", "E06"]:
    for w in ("t1", "t2"):
        x = ent(e, w, "venice", "VEN"); print(f"  {e} {w} money {x.get('money')} total {x.get('total')} ratio {float(x['money'])/float(x['total']):.4f}")
print("E02 monarch 11792 skills:")
for e in ["E01d", "E02"]:
    t = text(save(e, "t1"))
    for m in re.finditer(r"\n\t+monarch=\{\n\t+id=\{\n\t+id=11792\n.*?\n\t+\}", t, re.S):
        pass
    hits = [m.start() for m in re.finditer(r"id=11792\n", t)]
    out = []
    for h in hits[:6]:
        seg = t[max(0, h - 600): h + 200]
        d = re.findall(r"\n\t+(ADM|DIP|MIL)=(\d+)", seg)
        if d: out.append(d[-3:])
    print("  ", e, out[:4])
print("P02 hangzhou node (weights, steerers):")
for e in ["E01c", "P02"]:
    n = nodes(save(e, "t1"))["hangzhou"]
    st = {t: (v.get("type"), v.get("steer_power")) for t, v in n.items() if isinstance(v, dict) and v.get("has_trader")}
    print(f"  {e} t1 steer_power={n.get('steer_power')} traders={st} outgoing={[o['target'] for o in TN['hangzhou']['outgoing']]}")
    n2 = nodes(save(e, "t2"))["hangzhou"]
    st2 = {t: (v.get("type"), v.get("steer_power")) for t, v in n2.items() if isinstance(v, dict) and v.get("has_trader")}
    print(f"  {e} t2 steer_power={n2.get('steer_power')} traders={st2}")
print("P06 california XAL:")
for e in ["E01c", "P06"]:
    for w in ("t1", "t2"):
        n = nodes(save(e, w))["california"]; x = n.get("XAL", {})
        print(f"  {e} {w} XAL {{k: x.get(k) for k in ('has_trader','type','steer_power','max_pow','val')}} -> ", {k: x.get(k) for k in ('has_trader','type','steer_power','max_pow','val')}, "node steer_power", n.get("steer_power"))
print("P03/P04: VEN venice max_demand, transfer_home_bonus, constantinople outgoing:")
for e in ["E01c", "P03", "P04"]:
    c = block(save(e, "t1"), "countries")["VEN"]
    print(f"  {e} venice max_demand {ent(e,'t1','venice','VEN').get('max_demand')} thb {c.get('transfer_home_bonus')} ragusa {[(k, ent(e,'t1','ragusa','VEN').get(k)) for k in ('type','steer_power','max_pow','max_demand')]} const {[(k, ent(e,'t1','constantinople','VEN').get(k)) for k in ('type','steer_power','max_pow')]}")
print("  constantinople outgoing:", [o["target"] for o in TN["constantinople"]["outgoing"]])
print("P01/E21/E23 status:", {k: v.get("ok") for k, v in json.load(open(Path(__file__).parents[1] / "out/STATUS.json")).items() if k in ("P01", "E21", "E23")})
