"""R12 final, script 4: node aggregates that contain power/collectors with no country entry ("stale aggregates").
Whole corpus (84 distinct saves). Run from backend/.
 S1 tags listed in top_power without an entry           S2 max  == p_pow + sum(max_pow - prev - province_power) over entries
 S3 retain_power == sum eff of collectors (total|has_capital)   S4 pull_power == rule B (steer or non-collecting with collect/steer downstream)
 S5 num_collectors == #entries with total|has_capital   S6 collector_power == retain_power   S7 total == sum(val)  (only the nodes above are explained here)
 S8 facts about AFA (U03..U05) and the ghost residuals."""
import sys, json
sys.path.insert(0, "scripts/research")
from collections import Counter, defaultdict
from final_r12_common import *

DOWN = {}
def down(n):
    if n not in DOWN:
        s = set()
        for t in OUT[n]: s.add(t); s |= down(t)
        DOWN[n] = s
    return DOWN[n]
for n in OUT: down(n)

c = Counter(); ex = defaultdict(list); resid = {}
for sid, date, kind, nodes in saves(distinct=True):
    ents_all = {}
    for n in nodes:
        for t, e in entries_of(n).items(): ents_all[(n["definitions"], t)] = e
    coll = defaultdict(set); stee = defaultdict(set)
    for (nid, t), e in ents_all.items():
        if "total" in e or e.get("has_capital"): coll[t].add(nid)
        if "type" in e: stee[t].add(nid)
    for n in nodes:
        nid = n["definitions"]; ents = entries_of(n)
        for tag, v in zip(lst(n.get("top_power")), lst(n.get("top_power_values"))):
            c["S1 top_power rows"] += 1
            if tag not in ents: ex["S1 top_power tag without entry"].append((sid, nid, tag, v))
        if "max" in n and "p_pow" in n:
            c["S2 nodes"] += 1
            s = sum(m3(e["max_pow"]) - m3(e.get("prev", 0)) - m3(e.get("province_power", 0)) for e in ents.values() if "max_pow" in e)
            d = m3(n["max"]) - m3(n["p_pow"]) - s
            if d == 0: c["S2 ok"] += 1
            else: ex["S2 max residual (milli)"].append((sid, nid, d))
        rp = m3(n.get("retain_power", 0)); pl = m3(n.get("pull_power", 0))
        reff = sum(m3(e.get("val", 0)) - m3(e.get("t_out", 0)) + m3(e.get("t_in", 0)) for e in ents.values() if "total" in e or e.get("has_capital"))
        c["S3 nodes"] += 1
        if rp == reff: c["S3 ok"] += 1
        else: ex["S3 retain_power residual"].append((sid, nid, rp - reff))
        if OUT[nid]:
            pull = 0
            for t, e in ents.items():
                eff = m3(e.get("val", 0)) - m3(e.get("t_out", 0)) + m3(e.get("t_in", 0))
                here = "total" in e or bool(e.get("has_capital"))
                if "type" in e or (not here and ((coll[t] | stee[t]) & DOWN[nid])): pull += eff
            c["S4 nodes with downstream"] += 1
            if n.get("pull_power") is None:
                c["S4 pull_power absent"] += 1; ex["S4 pull_power absent, rule B gives"].append((sid, nid, pull)) if pull != 0 else None
            elif pl == pull: c["S4 ok"] += 1
            else: ex["S4 pull_power residual"].append((sid, nid, pl - pull))
        if "num_collectors" in n:
            k = sum(1 for e in ents.values() if "total" in e or e.get("has_capital"))
            c["S5 nodes"] += 1
            if n["num_collectors"] == k: c["S5 ok"] += 1
            else: ex["S5 num_collectors vs entries"].append((sid, nid, n["num_collectors"], k))
        if "collector_power" in n:
            c["S6 nodes"] += 1
            if m3(n["collector_power"]) == rp: c["S6 ok"] += 1
            else: ex["S6 collector_power - retain_power"].append((sid, nid, m3(n["collector_power"]) - rp))
        if "total" in n and (sid, nid) in {("S64", "genua"), ("U05", "ethiopia"), ("U05", "gulf_of_aden")}:
            resid[(sid, nid)] = m3(n["total"]) - sum(m3(e.get("val", 0)) for e in ents.values())

print(dict(c))
for k, v in ex.items(): print("EXCEPTIONS", k, len(v), v[:12])
print("total - sum(val) at the ghost nodes (milli):", resid)

# S64 genua: power_fraction denominator is collector_power
for sid, date, kind, nodes in saves(distinct=True):
    if sid != "S64": continue
    n = [x for x in nodes if x["definitions"] == "genua"][0]; cp = m3(n["collector_power"]); ok = 0; tot = 0
    for t, e in entries_of(n).items():
        if "power_fraction" in e:
            tot += 1; eff = m3(e["val"]) - m3(e.get("t_out", 0)) + m3(e.get("t_in", 0)); ok += m3(e["power_fraction"]) == (eff * 1000) // cp
    print("S64 genua: power_fraction = trunc3(eff / collector_power) in", ok, "of", tot, "; collector_power", cp, "retain_power", m3(n["retain_power"]), "num_collectors", n["num_collectors"])

# S8: AFA in U03/U04/U05
ents_by = {e["id"]: e for e in common.entries()}
for sid in ("U03", "U04", "U05"):
    e = ents_by[sid]; N = common.nodes(e); C = common.block(e, "countries"); a = C["AFA"]
    row = {"date": e["date"], "num_of_cities": a.get("num_of_cities"), "development": a.get("development")}
    for nid in ("ethiopia", "gulf_of_aden"):
        n = [x for x in N if x["definitions"] == nid][0]; x = n.get("AFA")
        row[nid] = None if x is None else {k: x[k] for k in ("type", "val", "max_pow", "max_demand", "province_power", "add", "has_capital", "has_trader", "total") if k in x}
        tp = dict(zip(lst(n.get("top_power")), lst(n.get("top_power_values"))))
        row[nid + " top_power AFA"] = tp.get("AFA")
    print(sid, json.dumps(row))
e = ents_by["U05"]; C = common.block(e, "countries"); P = common.block(e, "provinces"); a = C["AFA"]
print("U05 AFA: effective_score_impact", a.get("effective_score_impact"), "| last_war_ended", a.get("last_war_ended"), "| modifier", a.get("modifier"), "| capital/trade_port", a.get("capital"), a.get("trade_port"))
h = P["-2764"]["history"]
print("U05 province 2764 (Ausa) history after 1690:", {k: v for k, v in h.items() if k[:1].isdigit() and k > "1690"}, "| owner", P["-2764"]["owner"], "controller", P["-2764"]["controller"])
e4 = ents_by["U04"]; P4 = common.block(e4, "provinces"); print("U04 province 2764: owner", P4["-2764"]["owner"], "controller", P4["-2764"]["controller"], "trade_power", P4["-2764"]["trade_power"])
