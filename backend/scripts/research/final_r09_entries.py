"""R09 final: whole-corpus check of every country-in-node (entry) field of the trade block (86 corpus entries, 84 distinct saves).
Independent code: raw parsed save keys and the graph only."""
import sys, math, json, collections
sys.path.insert(0, "scripts/research")
import final_r09_load as L
from final_r09_chk import Rec

R = Rec(); f = L.fl
H = collections.defaultdict(collections.Counter)        # histograms
def hist(name, key, dup):
    if not dup: H[name][key] += 1
tr3 = L.tr3
MERCH = 2.0; CAPP = 5.0
for sid in L.IDS:
    dup = sid in L.DUP
    grp = "played" if sid in ("S79", "S80", "U01", "U02", "U03", "U04", "U05", "U06") else "start"
    ns = L.nodes(sid); byid = {n["definitions"]: n for n in ns}
    pp = {}                                                     # (node, tag) -> province_power
    for n in ns:
        for t, c in L.entries_of(n).items():
            if "province_power" in c: pp[(n["definitions"], t)] = c["province_power"]
    for n in ns:
        nid = n["definitions"]; es = L.entries_of(n)
        rp = n.get("retain_power", 0.0); cur = n.get("current", 0.0); tot = n.get("total")
        # ---------- prev rule over every (node, tag) pair with a possible or a recorded prev
        tags = set(es)
        for d in L.OUT[nid]:
            tags |= {t for (nn, t), v in pp.items() if nn == d and v >= 10}
        sw = L.lst(n.get("steer_power", []))
        for t in tags:
            pred = sum(tr3(pp.get((d, t), 0.0) / 5) for d in L.OUT[nid] if pp.get((d, t), 0.0) >= 10)
            predg = sum(tr3(pp.get((d, t), 0.0) / 5) for li, d in enumerate(L.OUT[nid]) if pp.get((d, t), 0.0) >= 10 and li < len(sw) and sw[li] > 0)
            rec_ = f(es.get(t, {}).get("prev"))
            e_ = es.get(t)
            if e_ is not None and ("max_pow" in e_ or "prev" in e_):
                R.rec(f"E04a prev, ungated: sum over outgoing links D of trunc3(province_power(tag,D)/5) where province_power(tag,D) >= 10 (absent = 0); entries that carry max_pow or prev [{grp} saves]", sid, abs(pred - rec_) <= 0.0015, (nid, t, round(pred, 3), rec_), dup)
            elif pred > 0:
                R.rec(f"E04b (node, tag) pairs where the ungated rule gives prev > 0 but the entry is missing or a max_demand-only stub [{grp} saves]", sid, False, (nid, t, round(pred, 3), "stub" if e_ is not None else "no entry"), dup)
            if pred > 0 or predg > 0 or rec_ > 0:
                R.rec(f"E04c prev, gated by the node's own link weight (link counts only if steer_power weight > 0), all (node, tag) pairs with pred or recorded prev > 0 [{grp} saves]", sid, abs(predg - rec_) <= 0.0015, (nid, t, round(predg, 3), rec_, "stub" if (e_ is not None and "max_pow" not in e_) else ("no entry" if e_ is None else "entry")), dup)
        for t, c in es.items():
            eff = f(c.get("val")) - f(c.get("t_out")) + f(c.get("t_in"))
            has = lambda k: k in c
            # ---------- stubs and max_demand
            R.rec("E01 max_demand present in every entry except potential-only stubs", sid, has("max_demand") or set(c) == {"potential"}, (nid, t, sorted(c)), dup)
            if has("max_demand"):
                hist("max_demand_range", "min" if False else None, dup)
            # ---------- val / max_pow
            if has("max_pow") and has("max_demand"):
                v = c.get("val")
                pred = tr3(c["max_pow"] * c["max_demand"])
                if v is None:
                    R.rec("E02b entries with max_pow but no val have max_pow <= 0 (val is floored at 0 and then omitted)", sid, c["max_pow"] <= 0, (nid, t, c["max_pow"], c["max_demand"]), dup)
                else:
                    R.rec("E02 val = trunc3(max_pow * max_demand)", sid, abs(v - pred) < 1e-9, (nid, t, v, c["max_pow"], c["max_demand"]), dup)
            if has("max_pow") and c["max_pow"] > 0 and has("max_demand"):
                R.rec("E02d every entry with max_pow > 0 has val", sid, has("val"), (nid, t, c["max_pow"], c["max_demand"]), dup)
            if has("val"):
                R.rec("E02c every entry with val has max_pow and max_demand", sid, has("max_pow") and has("max_demand"), (nid, t), dup)
            if has("max_pow"):
                ship = f(c.get("ship_power")); extras = round(c["max_pow"] - f(c.get("province_power")) - ship - f(c.get("prev")), 3)
                mods = L.lst(c.get("modifier", []))
                modsum = sum(f(m.get("power")) for m in mods)
                pred = (CAPP if c.get("has_capital") else 0.0) + (MERCH if (c.get("has_trader") and has("total") and not c.get("has_capital")) else 0.0) + modsum
                d = round(pred - extras, 3)
                hist(f"raw_power pred-recorded [{grp}]", d, dup)
                hist("raw_power recorded extras", extras, dup)
                R.rec("E03 max_pow = province_power + ship_power + prev + extras (extras residual: see histogram)", sid, True, (), dup)
                R.rec(f"E03b extras = 5*[has_capital] + 2*[has_trader & total & not has_capital] + sum(modifier.power) [{grp} saves]", sid, abs(d) < 0.0005, (nid, t, d), dup)
            # ---------- collecting triple
            if has("total") or has("power_fraction") or has("money"):
                R.rec("E05 total, power_fraction and money keys are present together", sid, has("total") and has("power_fraction") and has("money"), (nid, t), dup)
            if has("power_fraction") and rp > 0:
                R.rec("E06 power_fraction = trunc3(eff / node.retain_power)", sid, abs(c["power_fraction"] - tr3(eff / rp)) < 1e-9, (nid, t, c["power_fraction"], round(eff, 3), rp), dup)
            if has("total") and has("power_fraction"):
                R.rec("E07 total (entry) = trunc3(node.current * power_fraction)", sid, abs(c["total"] - tr3(cur * c["power_fraction"])) < 1e-9, (nid, t, c["total"], cur, c["power_fraction"]), dup)
                R.rec("E08 money >= total (entry)", sid, c.get("money", 0) >= c["total"] - 0.0005, (nid, t, c.get("money"), c["total"]), dup)
                if c["total"] > 0:
                    hist("money/total ratio rounded 0.01", round(c.get("money", 0) / c["total"], 2) if c["total"] >= 0.5 else "total<0.5", dup)
            # ---------- flags
            hist("flags (has_trader,type,total,has_capital)", (has("has_trader"), has("type"), has("total"), bool(c.get("has_capital"))), dup)
            if has("has_trader"): hist("has_trader values", repr(c["has_trader"]), dup)
            if has("has_capital"): hist("has_capital values", repr(c["has_capital"]), dup)
            if has("type"): hist("type values", repr(c["type"]), dup)
            if has("steer_power"):
                hist("entry steer_power values", repr(c["steer_power"]) if nid not in () else None, dup)
                R.rec("E09 entry steer_power is an index < out-degree of the node", sid, isinstance(c["steer_power"], int) and 0 <= c["steer_power"] < max(1, len(L.OUT[nid])), (nid, t, c["steer_power"], len(L.OUT[nid])), dup)
            hist("steering keys (type,steer_power,add)", (has("type"), has("steer_power"), has("add")), dup)
            if has("add"):
                hist("add range", "0<add<0.2" if 0 < c["add"] < 0.2 else "other", dup)
            # ---------- potential
            if has("potential"):
                if has("t_in") or has("t_out"):
                    if tot:
                        x = (f(c.get("t_out")) - f(c.get("t_in"))) / tot
                        R.rec("E10 potential = trunc3((t_out - t_in)/node.total) for entries with t_in or t_out (trunc toward zero)", sid, abs(c["potential"] - tr3(x)) < 1e-9, (nid, t, c["potential"], c.get("t_out"), c.get("t_in"), tot), dup)
                else:
                    hist("potential without transfer", (nid, t == "PIR", c["potential"]), dup)
            # ---------- transfers
            if has("t_out"):
                R.rec("E11 t_out = sum of t_to values", sid, abs(c["t_out"] - sum(c["t_to"].values())) < 0.0015, (nid, t, c["t_out"], c["t_to"]), dup)
                R.rec("E11b t_out and t_to come together", sid, has("t_to"), (nid, t), dup)
                R.rec("E11c t_out = trunc3(0.5*(val - 0.1)) (giver)", sid, abs(c["t_out"] - tr3(0.5 * (f(c.get("val")) - 0.1))) < 0.0015, (nid, t, c["t_out"], c.get("val")), dup)
                for rcv, amt in c["t_to"].items():
                    rc = es.get(rcv, {})
                    R.rec("E12 each t_to[B]=x has B.t_from[A]=x in the same node", sid, abs(f(rc.get("t_from", {}).get(t)) - amt) < 0.0015, (nid, t, rcv, amt, rc.get("t_from")), dup)
            if has("t_in"):
                R.rec("E13 t_in = sum of t_from values", sid, abs(c["t_in"] - sum(c["t_from"].values())) < 0.0015, (nid, t, c["t_in"], c["t_from"]), dup)
                R.rec("E13b t_in and t_from come together", sid, has("t_from"), (nid, t), dup)
                for giver, amt in c["t_from"].items():
                    gc = es.get(giver, {})
                    R.rec("E13c each t_from[A]=x has A.t_to[B]=x in the same node", sid, abs(f(gc.get("t_to", {}).get(t)) - amt) < 0.0015, (nid, t, giver, amt, gc.get("t_to")), dup)
            # ---------- ships
            if has("ship_power") or has("light_ship"):
                R.rec("E14 ship_power and light_ship come together", sid, has("ship_power") and has("light_ship"), (nid, t), dup)
                if has("ship_power") and has("light_ship") and c["light_ship"] > 0:
                    hist("ship_power per light_ship", round(c["ship_power"] / c["light_ship"], 3), dup)
            # ---------- modifier
            for m in L.lst(c.get("modifier", [])):
                hist("modifier key/power/power_modifier", (m.get("key"), m.get("power"), m.get("power_modifier")), dup)
            # ---------- province_power present only with max_pow?
            if has("province_power"):
                R.rec("E15 province_power only on entries with max_pow (and province_power > 0)", sid, has("max_pow") and c["province_power"] > 0, (nid, t, c["province_power"]), dup)
            if has("prev"):
                R.rec("E15b prev only on entries with max_pow", sid, has("max_pow"), (nid, t), dup)
            if has("max_pow"):
                R.rec("E15c max_pow entries all have max_demand, and val unless val would be 0", sid, has("max_demand"), (nid, t), dup)
R.report(maxex=10)
for k, v in H.items():
    items = sorted(v.items(), key=lambda x: -x[1])
    print("HIST", k, "(distinct saves)", len(items), "values:", items[:40])
R.dump("/tmp/eu4research/final_r09/entries.json")
json.dump({k: sorted(((str(a), b) for a, b in v.items()), key=lambda x: -x[1]) for k, v in H.items()}, open("/tmp/eu4research/final_r09/entries_hist.json", "w"))
