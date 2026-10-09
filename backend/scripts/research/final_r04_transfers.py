"""R04 final, script 1: t_out, t_to, t_in, t_from, potential, power_fraction over ALL manifest saves (independent code)."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r04_common as F

tot = Counter()          # all 86 entries
dist = Counter()         # distinct saves only (U01/U02 excluded)
exc = defaultdict(list)
vals_min = {}
nsave = 0
giver_tags = set()
offsets = Counter()
offset_by_bucket = defaultdict(Counter)
nodes_checked = Counter()
for sid, e, nodes in F.saves():
    isdup = sid in F.COPY_OF
    C = Counter()
    recv_expected = defaultdict(lambda: defaultdict(int))      # (node, recv) -> {giver: amount_m}
    for n in nodes:
        nid = n["definitions"]
        total_m = F.m(n["total"]) if "total" in n else None
        retain_m = F.m(n["retain_power"]) if "retain_power" in n else None
        has_transfer = False
        for tag, c in F.entries_of(n).items():
            C["entries"] += 1
            tin = F.m(c["t_in"]) if "t_in" in c else None
            tout = F.m(c["t_out"]) if "t_out" in c else None
            val = F.m(c["val"]) if "val" in c else None
            if tout is not None:
                has_transfer = True
                C["givers"] += 1
                giver_tags.add(tag)
                if val is None:
                    C["giver_no_val"] += 1; exc["giver_no_val"].append((sid, nid, tag)); continue
                exact = (val - 100) // 2
                if tout == exact: C["tout_ok"] += 1
                else: exc["tout"].append((sid, nid, tag, val, tout, exact))
                if tout == val // 2: C["tout_plain_half"] += 1
                if tout == (val - 100 + 1) // 2: C["tout_round_half_up"] += 1          # round-half-up of (val-100)/2
                if tout == round((val - 100) / 2): C["tout_round_py"] += 1
                off = val - 2 * tout
                offsets[off] += 1
                b = len(str(val // 1000)) if val >= 1000 else 0
                offset_by_bucket[b][off] += 1
                vals_min[(sid, nid, tag)] = val
                if "prev" in c: C["giver_with_prev"] += 1
                if c.get("prev") and off in (100, 101): C["giver_prev_ok"] += 1
                # t_to
                tt = c.get("t_to")
                if isinstance(tt, dict) and len(tt) == 1:
                    C["tto_one_key"] += 1
                    (r, amt), = tt.items()
                    if F.m(amt) == tout: C["tto_eq_tout"] += 1
                    else: exc["tto_amt"].append((sid, nid, tag, tt, tout))
                    recv_expected[(nid, r)][tag] = tout
                else:
                    exc["tto_shape"].append((sid, nid, tag, tt))
                if tin is not None: C["both_in_out"] += 1; exc["both"].append((sid, nid, tag))
            if tin is not None:
                has_transfer = True
                C["receivers"] += 1
                tf = c.get("t_from")
                if isinstance(tf, dict) and sum(F.m(v) for v in tf.values()) == tin: C["tin_eq_sum_tfrom"] += 1
                else: exc["tin_sum"].append((sid, nid, tag, tf, tin))
                if val is None: C["receiver_no_val"] += 1
                if "max_pow" in c and "max_demand" in c and val is not None:
                    C["recv_with_maxpow"] += 1
                    mp, md = F.m(c["max_pow"]), F.m(c["max_demand"])
                    # val = trunc3(max_pow * max_demand) -> in thousandths: mp*md/1000 truncated
                    if (mp * md) // 1000 == val: C["recv_val_eq_mp_md"] += 1
                    else: exc["recv_val"].append((sid, nid, tag, mp, md, val))
                    if ((mp * md) // 1000) + tin == val: C["recv_val_includes_tin"] += 1
            # val of every entry with max_pow
            if "potential" in c:
                C["potential_entries"] += 1
                p = F.m(c["potential"])
                tr = tout or 0; ti = tin or 0
                if total_m:
                    exp = F.trunc_div((tr - ti) * 1000, total_m)
                    fl = ((tr - ti) * 1000) // total_m
                    rd = (((tr - ti) * 1000 * 2 + total_m) // (2 * total_m))
                    C["pot_with_total"] += 1
                    if p == exp: C["pot_trunc0"] += 1
                    else: exc["pot"].append((sid, nid, tag, p, exp, tr, ti, total_m))
                    if p == fl: C["pot_floor"] += 1
                    if p == rd: C["pot_round_half_up"] += 1
                    if (tr or ti) == 0: C["pot_without_transfer_in_total_node"] += 1
                    if (tr or ti) and p == 0: C["pot_zero_with_transfer"] += 1
                    if retain_m and p == F.trunc_div((tr - ti) * 1000, retain_m): C["pot_den_retain"] += 1
                else:
                    C["pot_no_total"] += 1
                    C["pot_no_total_" + nid] += 1
                    if tr or ti: C["pot_no_total_with_transfer"] += 1
                    C["pot_no_total_val_" + str(p)] += 1
            elif (tout or tin):
                C["transfer_without_potential"] += 1
                if total_m: exc["no_pot"].append((sid, nid, tag))
            # power fraction for collectors that take part in a transfer
            if "power_fraction" in c and (tout or tin) and retain_m:
                C["pf_transfer_entries"] += 1
                eff = (val or 0) - (tout or 0) + (tin or 0)
                exp = F.trunc_div(eff * 1000, retain_m)
                if F.m(c["power_fraction"]) == exp: C["pf_transfer_ok"] += 1
                else: exc["pf"].append((sid, nid, tag, c["power_fraction"], exp, eff, retain_m))
                if tout: C["pf_giver"] += 1; C["pf_giver_ok"] += (F.m(c["power_fraction"]) == exp)
                if tin: C["pf_recv"] += 1; C["pf_recv_ok"] += (F.m(c["power_fraction"]) == exp)
                if tout and val is not None and F.m(c["power_fraction"]) == F.trunc_div(val * 1000, retain_m): C["pf_giver_plain_val"] += 1
        if has_transfer:
            C["nodes_with_transfer"] += 1
            # retain_power = sum of eff of collectors, in such nodes
            if retain_m is not None:
                s = 0
                for tag, c in F.entries_of(n).items():
                    if "total" in c or c.get("has_capital"):
                        s += (F.m(c["val"]) if "val" in c else 0) - (F.m(c["t_out"]) if "t_out" in c else 0) + (F.m(c["t_in"]) if "t_in" in c else 0)
                C["retain_nodes_with_transfer"] += 1
                if abs(s - retain_m) <= 10: C["retain_ok_with_transfer"] += 1
                else: exc["retain"].append((sid, nid, s, retain_m))
    # receivers vs expected
    for (nid, r), gm in recv_expected.items():
        n = [x for x in nodes if x["definitions"] == nid][0]
        c = n.get(r)
        if not isinstance(c, dict) or "t_from" not in c:
            C["recv_missing"] += 1; exc["recv_missing"].append((sid, nid, r)); continue
        C["recv_checked"] += 1
        got = {k: F.m(v) for k, v in c["t_from"].items()}
        if got == gm and F.m(c.get("t_in")) == sum(gm.values()): C["recv_ok"] += 1
        else: exc["recv_mismatch"].append((sid, nid, r, got, gm))
    # every receiver entry has a matching giver
    for n in nodes:
        for tag, c in F.entries_of(n).items():
            if "t_in" in c:
                for g in c.get("t_from", {}):
                    cg = n.get(g)
                    if not (isinstance(cg, dict) and "t_to" in cg and tag in cg["t_to"]): exc["from_without_to"].append((sid, n["definitions"], tag, g))
                    else: C["tfrom_has_tto"] += 1
    tot.update(C)
    if not isdup: dist.update(C)
    nsave += 1

print("manifest entries", nsave, "distinct", nsave - len(F.COPY_OF))
for name, cnt in (("ALL 86 entries", tot), ("84 DISTINCT saves", dist)):
    print("==", name)
    for k in sorted(cnt):
        if k.startswith("pot_no_total_") : continue
        print(f"  {k}: {cnt[k]}")
    print("  pot_no_total breakdown:", {k: v for k, v in cnt.items() if k.startswith("pot_no_total_")})
print("giver tags", len(giver_tags), sorted(giver_tags))
print("offset val-2*t_out (thousandths):", dict(offsets))
print("offset by magnitude bucket:", {b: dict(c) for b, c in sorted(offset_by_bucket.items())})
mv = sorted(vals_min.items(), key=lambda kv: kv[1])[:5]
print("smallest giver vals:", mv)
print("givers with val<2000:", sum(1 for v in vals_min.values() if v < 2000), "of", len(vals_min))
for k, v in exc.items():
    print("EXC", k, len(v), v[:12])
