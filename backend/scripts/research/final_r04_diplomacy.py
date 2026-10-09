"""R04 final, script 9: top-level `diplomacy` block: `transfer_trade_power={amount is_enforced first second start_date}` and
`dependency={first second start_date subject_type}` versus country-block flag and node t_out. Independent code."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r04_common as F
import common
from app.parsing.clausewitz import as_list

def dnum(s):
    y, mo, d = (int(x) for x in str(s).split("."))
    return (y, mo, d)

tot = Counter(); dist = Counter(); exc = defaultdict(list)
amounts = Counter(); enforced = Counter(); types_rec = Counter(); types_all = Counter(); types_giver = Counter()
timing = []
for e in common.entries():
    sid = e["id"]; dup = sid in F.COPY_OF
    nodes = common.nodes(e)
    cb = common.block(e, "countries")
    dip = common.block(e, "diplomacy")
    gave = defaultdict(int); hasval = defaultdict(int)
    for n in nodes:
        for tag, c in F.entries_of(n).items():
            if "val" in c: hasval[tag] += 1
            if "t_out" in c: gave[tag] += 1
    recs = {}
    C = Counter()
    for r in as_list(dip.get("transfer_trade_power")):
        if not isinstance(r, dict): continue
        C["records"] += 1
        amounts[(r.get("amount"))] += 1; enforced[r.get("is_enforced")] += 1
        g = r["first"]
        if g in recs: C["record_dup_giver"] += 1
        recs[g] = r
    deps = {}
    for r in as_list(dip.get("dependency")):
        if isinstance(r, dict): deps[r["second"]] = r
    # record <-> flag
    flagged = {t for t, cd in cb.items() if isinstance(cd, dict) and "transfer_trade_power_to" in cd}
    C["rec_eq_flag_sets"] += (set(recs) == flagged)
    if set(recs) != flagged: exc["rec_vs_flag"].append((sid, sorted(set(recs) ^ flagged)))
    for g, r in recs.items():
        ov = cb.get(g, {}).get("overlord") if isinstance(cb.get(g), dict) else None
        C["rec_second_eq_overlord"] += (r["second"] == ov)
        if r["second"] != ov: exc["rec_second"].append((sid, g, r["second"], ov))
        d = deps.get(g)
        if d and d["first"] == r["second"]:
            C["rec_has_dependency"] += 1; types_rec[d["subject_type"]] += 1
            C["rec_start_eq_dep_start"] += (d["start_date"] == r["start_date"])
            if d["start_date"] != r["start_date"]: exc["start_mismatch"].append((sid, g, d["start_date"], r["start_date"]))
        else: C["rec_without_dependency"] += 1; exc["rec_no_dep"].append((sid, g))
        if hasval.get(g):
            C["rec_entries"] += 1
            C["rec_and_tout"] += bool(gave.get(g))
            if not gave.get(g): exc["rec_no_tout"].append((sid, g, r["start_date"], e["date"]))
    for g in gave:
        if g not in recs: C["tout_without_record"] += 1; exc["tout_no_rec"].append((sid, g))
    # subject types vs giver
    for s, d in deps.items():
        if not hasval.get(s): continue
        types_all[d["subject_type"]] += 1
        if gave.get(s): types_giver[d["subject_type"]] += 1
        C["dep_" + d["subject_type"] + ("_giver" if gave.get(s) else "_nongiver")] += 1
        if s not in recs: C["dep_without_record_" + d["subject_type"]] += 1
        if d["subject_type"] in ("colony", "trade_protectorate") and s not in recs: exc["colony_tp_without_record"].append((sid, s, d["subject_type"], d["first"]))
    # record without t_out: dates
    tot.update(C)
    if not dup: dist.update(C)
for nm, c in (("ALL 86 entries", tot), ("84 DISTINCT", dist)):
    print("==", nm)
    for k in sorted(c): print(f"  {k}: {c[k]}")
print("amount values (all records, 86 entries):", dict(amounts)); print("is_enforced:", dict(enforced))
print("types among records:", dict(types_rec)); print("dependencies by type with val entries (86):", dict(types_all), "givers:", dict(types_giver))
for k, v in exc.items(): print("EXC", k, len(v), v[:12])
