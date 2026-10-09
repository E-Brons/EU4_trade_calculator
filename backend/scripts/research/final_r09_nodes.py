"""R09 final: whole-corpus check of every node-level field of the trade block (86 corpus entries, 84 distinct saves).
Independent code: raw parsed save keys + the graph in data/tradenodes.json only (no app.trade.calc)."""
import sys, math, json, collections
sys.path.insert(0, "scripts/research")
import final_r09_load as L
from final_r09_chk import Rec

R = Rec()
PR = json.load(open("/tmp/eu4research/final_r09/change_price.json"))
ceil3 = lambda x: math.ceil(x * 1000 - 1e-6) / 1000
f = L.fl
ORDER0 = None
TCR = collections.defaultdict(collections.Counter)      # node -> Counter of trade_company_region values
for sid in L.IDS:
    dup = sid in L.DUP
    ns = L.nodes(sid)
    ids = [n["definitions"] for n in ns]
    if ORDER0 is None: ORDER0 = ids
    R.rec("NK01 80 nodes, id set = graph node set (per save)", sid, len(ns) == 80 and set(ids) == set(L.OUT), (len(ns),), dup)
    R.rec("NK02 node order identical to S01 (per save)", sid, ids == ORDER0, (), dup)
    byid = {n["definitions"]: n for n in ns}
    price = [p for _, p in PR[sid]]
    coll = collections.defaultdict(set); steer = collections.defaultdict(set)
    ents = {}
    for n in ns:
        for t, c in L.entries_of(n).items():
            ents[(n["definitions"], t)] = c
            if "total" in c or c.get("has_capital"): coll[t].add(n["definitions"])
            if "type" in c: steer[t].add(n["definitions"])
    for n in ns:
        nid = n["definitions"]; es = L.entries_of(n); end = nid in L.END_NODES
        eff = {t: f(c.get("val")) - f(c.get("t_out")) + f(c.get("t_in")) for t, c in es.items()}
        collects = {t for t, c in es.items() if "total" in c or c.get("has_capital")}
        rp_calc = sum(eff[t] for t in collects)
        # pulling by rule B of R03 final (steers, or non-collector with a collect/steer node downstream)
        pulls = {t for t, c in es.items() if "type" in c or (t not in collects and ((coll[t] | steer[t]) & L.downstream(nid)))}
        pp_calc = sum(eff[t] for t in pulls)
        ret = n["retention"]; rp = n.get("retain_power", 0.0); pl = n.get("pull_power", 0.0)
        q = rp / (rp + pl) if rp + pl > 0 else 1.0
        inc = L.lst(n.get("incoming", []))
        gross = round(f(n.get("local_value")) + sum(i["value"] for i in inc), 3)
        cur = n.get("current", 0.0); out = n.get("outgoing", 0.0)
        # ---- incoming
        froms = [i["from"] for i in inc]
        okfrom = all(isinstance(x, int) and 1 <= x <= 80 and ids[x - 1] in L.INC[nid] for x in froms) and len(set(froms)) == len(froms)
        R.rec("NK03 incoming[].from (1-based) names a graph upstream node, no repeats (per node with incoming)", sid, okfrom or not inc, (nid, froms), dup) if inc else None
        for u in L.INC[nid]:
            has = any(ids[i["from"] - 1] == u for i in inc)
            uo = byid[u].get("outgoing", 0.0)
            R.rec("NK03b link slot (upstream->node) without incoming element has upstream outgoing = 0 or weight 0", sid,
                  has or uo <= 0.0015 or byid[u]["steer_power"][L.OUT[u].index(nid)] == 0, (u, nid, uo), dup)
        # ---- value fields
        if not end:
            R.rec("NK04 outgoing = round3(gross - current) (absent = 0)", sid, abs(out - round(gross - cur, 3)) < 1e-9, (nid, gross, cur, out), dup)
            R.rec("NK05 value_added_outgoing == outgoing (both absent or equal)", sid, n.get("value_added_outgoing", 0.0) == out and (("value_added_outgoing" in n) == ("outgoing" in n)), (nid, out, n.get("value_added_outgoing")), dup)
        else:
            R.rec("NK04b end node: no outgoing, no value_added_outgoing, no pull_power, no steer_power", sid, not any(k in n for k in ("outgoing", "value_added_outgoing", "pull_power", "steer_power")), (nid,), dup)
        R.rec("NK06 current = ceil3(gross * retention)  (gross = local_value + sum incoming.value; absent = 0)", sid, abs(cur - ceil3(gross * ret)) < 1e-9, (nid, gross, ret, cur, out, len(L.OUT[nid])), dup)
        R.rec("NK07 retention = ceil3(retain/(retain+pull)), 1.0 when both 0", sid, abs(ret - ceil3(q)) < 1e-9, (nid, q, ret), dup)
        # ---- powers
        R.rec("NK08 retain_power = sum eff(val-t_out+t_in) over entries with total or has_capital (absent = 0)", sid, abs(rp_calc - rp) < 0.0004, (nid, round(rp_calc, 3), rp), dup)
        if not end:
            R.rec("NK09 pull_power = sum eff of pulling entries, rule B of R03 final (absent = 0)", sid, abs(pp_calc - pl) < 0.0004, (nid, round(pp_calc, 3), pl), dup)
        ntot = sum(1 for c in es.values() if "total" in c)
        R.rec("NK10 num_collectors = #entries with key total (absent = 0)", sid, n.get("num_collectors", 0) == ntot, (nid, n.get("num_collectors", 0), ntot), dup)
        R.rec("NK10b num_collectors = #entries with total or has_capital", sid, n.get("num_collectors", 0) == len(collects), (nid, n.get("num_collectors", 0), len(collects)), dup)
        R.rec("NK11 num_collectors_including_pirates = num_collectors + 1", sid, n["num_collectors_including_pirates"] == n.get("num_collectors", 0) + 1, (nid, n["num_collectors_including_pirates"], n.get("num_collectors", 0)), dup)
        R.rec("NK11b PIR entry present and holds only max_demand", sid, "PIR" in es and set(es["PIR"]) <= {"max_demand", "potential"}, (nid,), dup)
        R.rec("NK12 collector_power = retain_power (absent = 0)", sid, n.get("collector_power", 0.0) == rp, (nid, n.get("collector_power"), rp), dup)
        R.rec("NK12b collector_power_including_pirates = collector_power", sid, n.get("collector_power_including_pirates", 0.0) == n.get("collector_power", 0.0), (nid,), dup)
        # ---- total, tops, max
        if "total" in n:
            sv = sum(f(c.get("val")) for c in es.values())
            R.rec("NK13 total = sum of entry val (exact at 3 decimals)", sid, abs(sv - n["total"]) < 0.0004, (nid, round(sv, 3), n["total"], round(n["total"] - sv, 3)), dup)
            pos = sorted(((e, t) for t, e in eff.items() if e > 0.0004), reverse=True)
            tp = L.lst(n.get("top_power", [])); tv = L.lst(n.get("top_power_values", []))
            okset = set(tp) == {t for _, t in pos} and len(tp) == len(tv)
            okval = okset and all(abs(v - eff[t]) < 0.0004 for t, v in zip(tp, tv))
            oksort = all(tv[i] >= tv[i + 1] for i in range(len(tv) - 1))
            R.rec("NK14 top_power = tags with eff > 0; top_power_values = their eff (val-t_out+t_in); sorted descending", sid, okset and okval and oksort, (nid, len(tp), len(pos), sorted(set(tp) ^ {t for _, t in pos})[:5]), dup)
            pps = sorted(((f(c.get("province_power")), t) for t, c in es.items() if f(c.get("province_power")) > 0), reverse=True)
            tpr = L.lst(n.get("top_provinces", [])); tpv = L.lst(n.get("top_provinces_values", []))
            okp = (set(tpr) == {t for _, t in pps} and len(tpr) == len(tpv) and all(abs(v - es[t]["province_power"]) < 0.0004 for t, v in zip(tpr, tpv))
                   and all(tpv[i] >= tpv[i + 1] for i in range(len(tpv) - 1)))
            R.rec("NK15 top_provinces = tags with province_power > 0; values = province_power; sorted descending (both keys absent when none)", sid, okp and (bool(pps) == ("top_provinces" in n)), (nid, len(tpr), len(pps)), dup)
        else:
            R.rec("NK13b node without total has no entries with power (all stubs)", sid, all(set(c) <= {"max_demand", "potential"} for c in es.values()), (nid,), dup)
        if "p_pow" in n:
            s_pp = sum(f(c.get("province_power")) for c in es.values())
            extra = sum(f(c.get("max_pow")) - f(c.get("prev")) - f(c.get("province_power")) for c in es.values())
            R.rec("NK16 max = p_pow + sum(max_pow - prev - province_power) (|d| <= 0.0105)", sid, abs(n["max"] - (n["p_pow"] + extra)) <= 0.0105, (nid, n["max"], round(n["p_pow"] + extra, 3), round(n["max"] - n["p_pow"] - extra, 3)), dup)
            R.rec("NK16b  same, |d| <= 0.0035", sid, abs(n["max"] - (n["p_pow"] + extra)) <= 0.0035, (nid, n["max"], round(n["p_pow"] + extra, 3), round(n["max"] - n["p_pow"] - extra, 3)), dup)
            R.rec("NK17 p_pow = sum of entry province_power (|d| <= 0.0105)", sid, abs(n["p_pow"] - s_pp) <= 0.0105, (nid, n["p_pow"], round(s_pp, 3), round(n["p_pow"] - s_pp, 3)), dup)
            R.rec("NK17b p_pow >= sum of entry province_power - 0.0105", sid, n["p_pow"] >= s_pp - 0.0105, (nid, n["p_pow"], round(s_pp, 3)), dup)
        # ---- steer_power (node) / misc
        if not end:
            sw = L.lst(n.get("steer_power", []))
            R.rec("NK19 steer_power has one weight per outgoing link (graph edge order length)", sid, len(sw) == len(L.OUT[nid]), (nid, len(sw), len(L.OUT[nid])), dup)
            R.rec("NK19b sum of weights in {0.998, 0.999, 1.000}, or all weights 0.0 (then no pull_power and no outgoing value)", sid, round(sum(sw), 3) in (0.998, 0.999, 1.0) or (sum(sw) == 0 and "pull_power" not in n), (nid, sw), dup)
            R.rec("NK19c all weights 0.0 only when the node has no steerer/puller power (pull_power absent) or outgoing = 0", sid, sum(sw) != 0 or "pull_power" not in n or out == 0, (nid, sw, out, n.get("pull_power")), dup)
        R.rec("NK20 most_recent_treasure_ship_passage = 1.1.1", sid, n["most_recent_treasure_ship_passage"] == "1.1.1", (nid, n["most_recent_treasure_ship_passage"]), dup)
        TCR[nid][str(n.get("trade_company_region", "absent"))] += 1
        gs = L.lst(n["trade_goods_size"])
        R.rec("NK21 trade_goods_size has 33 numbers >= 0", sid, len(gs) == 33 and all(x >= 0 for x in gs), (nid, len(gs)), dup)
        lv = f(n.get("local_value"))
        s = sum(a * p for a, p in zip(gs, price)) / 12
        inc_in = gs[26] > 0
        if not inc_in:
            R.rec("NK22 local_value = sum(size_i * price_i)/12 (|d|<=0.002), nodes without incense (absent = 0)", sid, abs(s - lv) <= 0.002, (nid, round(s, 4), lv), dup)
        elif nid == "australia":
            R.rec("NK22a local_value plain formula, node australia (0.6 incense)", sid, abs(s - lv) <= 0.002, (nid, round(s, 4), lv), dup)
        else:
            R.rec("NK22b local_value with incense valued 1.1 x price (incense nodes except australia)", sid, abs(s + 0.1 * gs[26] * price[26] / 12 - lv) <= 0.002, (nid, round(s, 4), lv), dup)
            R.rec("NK22c   same nodes, plain formula (shows the premium exists)", sid, abs(s - lv) <= 0.002, (nid, round(s, 4), lv), dup)
    # ---- link identities (R08 C-06): incoming.value - incoming.add = outgoing * w_L ; add = outgoing*w*sum(add)
    for n in ns:
        nid = n["definitions"]
        if nid in L.END_NODES or "steer_power" not in n: continue
        sw = L.lst(n["steer_power"]); out = n.get("outgoing", 0.0)
        for li, tgt in enumerate(L.OUT[nid]):
            w = sw[li] if li < len(sw) else 0.0
            inc = [i for i in L.lst(byid[tgt].get("incoming", [])) if ids[i["from"] - 1] == nid]
            v = sum(i["value"] for i in inc); a = sum(i["add"] for i in inc)
            R.rec("NK23 link: outgoing*w - 0.002 <= incoming.value - incoming.add <= outgoing*(w+0.001) + 0.002", sid, out * w - 0.002 <= v - a <= out * (w + 0.001) + 0.002, (nid, tgt, out, w, v, a), dup)
            addsum = sum(f(c.get("add")) for (nn, t), c in ents.items() if nn == nid and "add" in c and c.get("steer_power", 0) == li)
            tol = 0.002 + 0.001 * out + 0.0006 * out * max(1, sum(1 for (nn, t), c in ents.items() if nn == nid and "add" in c and c.get("steer_power", 0) == li))
            R.rec("NK24 link: incoming.add = outgoing * w * (sum of add of entries with key add and steer_power = link index)", sid, abs(a - out * w * addsum) <= tol + 0.001, (nid, tgt, out, w, addsum, a), dup)
R.report(maxex=14)
print("trade_company_region values per node (how many nodes show value sets):", collections.Counter(tuple(sorted(c)) for c in TCR.values()))
print("trade_company_region nodes always True / always absent / mixed:",
      sum(1 for c in TCR.values() if set(c) == {"True"}), sum(1 for c in TCR.values() if set(c) == {"absent"}), [ (k, dict(c)) for k, c in TCR.items() if len(c) > 1])
R.dump("/tmp/eu4research/final_r09/nodes.json")
