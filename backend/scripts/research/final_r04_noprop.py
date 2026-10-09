"""R04 final, script 5: do transfers propagate upstream? Test on `prev` of entries whose direct downstream node holds a giver (t_out) or receiver (t_in)
entry of the same tag. H1: prev = sum over links B->D with province_power_D>=10 of trunc3(province_power_D/5) (giver's/receiver's full own province power).
H2 (giver): province_power reduced by the given share, pp*(val-t_out)/val. H3 (receiver): H1 plus trunc3(t_in_D/5). Links: ungated, and gated by steer_power weight > 0."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r04_common as F
from app.parsing.tradenodes import load_trade_graph
G = load_trade_graph()
tot = Counter(); dist = Counter(); exc = defaultdict(list)
for sid, e, nodes in F.saves():
    dup = sid in F.COPY_OF
    byid = {n["definitions"]: n for n in nodes}
    pp = {}
    for n in nodes:
        for tag, c in F.entries_of(n).items():
            if "province_power" in c: pp[(n["definitions"], tag)] = c
    C = Counter()
    for B, n in byid.items():
        if B not in G: continue
        outs = list(G.outgoing(B)); sp = n.get("steer_power")
        if not isinstance(sp, list): sp = [1.0] * len(outs)
        cand = defaultdict(list)       # tag -> [(D, weight, c_D)]
        for i, D in enumerate(outs):
            w = sp[i] if i < len(sp) else 0
            for (nid, tag), c in pp.items():
                pass
        # faster: iterate downstream nodes' entries
        for i, D in enumerate(outs):
            w = sp[i] if i < len(sp) else 0
            dn = byid.get(D)
            if not dn: continue
            for tag, c in F.entries_of(dn).items():
                if "province_power" in c and F.m(c["province_power"]) >= 10000:
                    cand[tag].append((D, w, c))
        for tag, lst in cand.items():
            own = n.get(tag); rec = F.m(own.get("prev", 0)) if isinstance(own, dict) else 0
            kinds = set()
            for D, w, c in lst:
                if "t_out" in c: kinds.add("giver")
                if "t_in" in c: kinds.add("receiver")
            kind = "+".join(sorted(kinds)) if kinds else "control"
            def pred(gated, mode):
                s = 0
                for D, w, c in lst:
                    if gated and not w > 0: continue
                    ppm = F.m(c["province_power"])
                    if mode == "H2" and "t_out" in c and "val" in c and F.m(c["val"]) > 0:
                        ppm = ppm * (F.m(c["val"]) - F.m(c["t_out"])) // F.m(c["val"])
                    s += ppm // 5
                    if mode == "H3" and "t_in" in c: s += F.m(c["t_in"]) // 5
                return s
            for gated in (False, True):
                for mode in ("H1", "H2", "H3"):
                    ok = abs(pred(gated, mode) - rec) <= 1
                    C[f"{kind}|{'gated' if gated else 'ungated'}|{mode}|ok"] += ok
            C[f"{kind}|n"] += 1
            for gated in (False, True):
                alt = "H2" if kind == "giver" else "H3"
                if kind in ("giver", "receiver") and abs(pred(gated, "H1") - pred(gated, alt)) > 1:
                    gn = "gated" if gated else "ungated"
                    C[f"{kind}|{gn}|discriminating"] += 1
                    C[f"{kind}|{gn}|disc_H1_ok"] += abs(pred(gated, "H1") - rec) <= 1
                    C[f"{kind}|{gn}|disc_alt_ok"] += abs(pred(gated, alt) - rec) <= 1
            if kind != "control":
                # record non-matches of H1 (either gate) for listing
                if abs(pred(False, "H1") - rec) > 1 and abs(pred(True, "H1") - rec) > 1:
                    exc["H1_both_gates_fail"].append((sid, B, tag, rec / 1000, pred(False, "H1") / 1000, pred(True, "H1") / 1000, kind))
    tot.update(C)
    if not dup: dist.update(C)
for nm, c in (("ALL 86 entries", tot), ("84 DISTINCT", dist)):
    print("==", nm)
    kinds = sorted({k.split("|")[0] for k in c})
    for kd in kinds:
        print(f"  {kd}: n={c[kd+'|n']}")
        for g in ("ungated", "gated"):
            print("     ", g, {m: c[f"{kd}|{g}|{m}|ok"] for m in ("H1", "H2", "H3")}, "discriminating", c[f"{kd}|{g}|discriminating"], "H1 ok", c[f"{kd}|{g}|disc_H1_ok"], "alt ok", c[f"{kd}|{g}|disc_alt_ok"])
for k, v in exc.items():
    print("EXC", k, len(v))
    for x in v[:25]: print("   ", x)
