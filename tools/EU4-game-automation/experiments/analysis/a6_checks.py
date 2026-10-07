"""Change-happened checks and province/country-level evidence per experiment."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); from common import block, save, nodes, m3, as_list

def C(eid, w, tag="VEN"): return block(save(eid, w), "countries").get(tag, {})
def P(eid, w, pid): return block(save(eid, w), "provinces").get(f"-{pid}", {})

def show(label, f):
    for eid in label:
        try: print(f"  {eid}:", f(eid))
        except Exception as e: print(f"  {eid}: ERR {e}")

print("E02 ruler DIP (monarch):")
def ruler(eid, w="t1"):
    c = C(eid, w); m = c.get("monarch")
    hist = c.get("history", {})
    return {"monarch_ref": m, "dip_tech": c.get("technology", {}).get("dip_tech"), "powers": c.get("powers")}
show(["E01d", "E02"], ruler)
for eid in ["E01d", "E02"]:
    t = Path(save(eid, "t1")).read_text(encoding="latin-1")
    import re
    i = t.index("\n\tVEN={", t.index("\ncountries={")); j = t.find("\n\t\tmonarch={", i)
    k = t.find("\n\t\t}", j); print("  ", eid, "monarch block:", re.sub(r"\s+", " ", t[j:k])[:400])
print("E10/E11 technology:")
show(["E01d", "E10", "E11"], lambda e: C(e, "t1").get("technology"))
print("E13/P04 merchants:")
show(["E01d", "E13", "P04", "E01c"], lambda e: (len(as_list((C(e, "t1").get("merchants") or {}).get("envoy"))), C(e, "t1").get("transfer_home_bonus")))
print("E22 idea groups:")
show(["E01a", "E22"], lambda e: C(e, "t1").get("active_idea_groups"))
print("E16/E17 Venezia (112):")
show(["E01d", "E16", "E17"], lambda e: {k: P(e, "t1", 112).get(k) for k in ("center_of_trade", "trade_power", "buildings", "trade_goods")})
print("E18 Padova (4729) t1/t2:")
show(["E01d", "E18"], lambda e: [{k: P(e, w, 4729).get(k) for k in ("local_autonomy", "trade_power")} for w in ("t1", "t2")])
print("E12 mercantilism, province 112 trade_power t1/t2:")
show(["E01d", "E12"], lambda e: [(C(e, w).get("mercantilism"), P(e, w, 112).get("trade_power")) for w in ("t1", "t2")])
print("E09 province 112 trade_power t1/t2:")
show(["E01d", "E09"], lambda e: [P(e, w, 112).get("trade_power") for w in ("t1", "t2")])
print("E19 capital/trade_port, venice has_capital:")
show(["E01d", "E19"], lambda e: [(C(e, w).get("capital"), C(e, w).get("trade_port"), nodes(save(e, w))["venice"]["VEN"].get("has_capital")) for w in ("t1", "t2")])
print("E15 Piedmont (103) base_production / trade_power:")
show(["E01d", "E15"], lambda e: [{k: P(e, w, 103).get(k) for k in ("base_production", "trade_power")} for w in ("t1", "t2")])
print("E20 MAN overlord / subjects:")
show(["E01d", "E20a", "E20b", "E20c", "E20d"], lambda e: {k: C(e, "t2", "MAN").get(k) for k in ("overlord", "is_subject", "subject_type")} | {"VEN_subjects": C(e, "t2").get("subjects")})
print("E20 MAN venice entry:")
show(["E01d", "E20a", "E20c", "E20d"], lambda e: {k: v for k, v in nodes(save(e, "t2"))["venice"]["MAN"].items()})
print("E14 modifier at ragusa:")
show(["E14"], lambda e: nodes(save(e, "t1"))["ragusa"]["VEN"].get("modifier"))
print("E07 VEN light ships / ship_power:")
show(["E01d", "E07"], lambda e: {k: nodes(save(e, "t1"))["venice"]["VEN"].get(k) for k in ("light_ship", "ship_power")})
