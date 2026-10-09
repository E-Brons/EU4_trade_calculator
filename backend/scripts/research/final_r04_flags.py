"""R04 final, script 2: who gives. Country block flag `transfer_trade_power_to` / `transfer_trade_power_from` / `overlord` vs node `t_out` (independent)."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r04_common as F
import common
from app.parsing.clausewitz import as_list

tot = Counter(); dist = Counter(); exc = defaultdict(list)
bei = []
subj_nongiver_examples = {}
for e in common.entries():
    sid = e["id"]; dup = sid in F.COPY_OF
    nodes = common.nodes(e)
    cb = common.block(e, "countries")
    # which tags have entries with val anywhere / t_out anywhere
    has_val = defaultdict(int); has_tout = defaultdict(int)
    for n in nodes:
        for tag, c in F.entries_of(n).items():
            if "val" in c: has_val[tag] += 1
            if "t_out" in c: has_tout[tag] += 1
    C = Counter()
    flagged = {}
    for tag, cd in cb.items():
        if not isinstance(cd, dict): continue
        fl = cd.get("transfer_trade_power_to")
        if fl is not None:
            flagged[tag] = as_list(fl)
    for tag in has_val:
        if tag == "---": continue
        cd = cb.get(tag)
        fl = flagged.get(tag)
        gave = has_tout[tag] > 0
        if gave and fl: C["flag_and_tout"] += 1
        elif gave and not fl: C["tout_no_flag"] += 1; exc["tout_no_flag"].append((sid, tag))
        elif fl and not gave:
            C["flag_no_tout"] += 1; exc["flag_no_tout"].append((sid, tag, has_val[tag], has_tout[tag], e["date"]))
        else: C["neither"] += 1
        if gave:
            ov = cd.get("overlord")
            tos = set()
            for n in nodes:
                c = n.get(tag)
                if isinstance(c, dict) and "t_to" in c: tos |= set(c["t_to"])
            C["giver_tto_eq_overlord"] += (tos == {ov}); 
            if tos != {ov}: exc["tto_ne_overlord"].append((sid, tag, tos, ov))
            C["giver_flag_eq_overlord"] += (fl == [ov] or fl == ov)
            if not (fl == [ov] or fl == ov): exc["flag_ne_overlord"].append((sid, tag, fl, ov))
            C["giver_countrysaves"] += 1
            ovd = cb.get(ov, {})
            frm = as_list(ovd.get("transfer_trade_power_from")) if isinstance(ovd, dict) else []
            C["overlord_lists_giver"] += (tag in frm)
            if tag not in frm: exc["overlord_not_listing"].append((sid, tag, ov))
            if "colonial_parent" in cd: C["giver_colonial"] += 1
            else: C["giver_noncolonial"] += 1; C["giver_noncolonial_" + tag] += 1
    # reverse: every tag in a transfer_trade_power_from list has the flag
    for tag, cd in cb.items():
        if isinstance(cd, dict) and "transfer_trade_power_from" in cd:
            for g in as_list(cd["transfer_trade_power_from"]):
                C["from_entries"] += 1
                if g in flagged and (flagged[g] == [tag]): C["from_matches_flag"] += 1
                else: exc["from_not_flag"].append((sid, tag, g, flagged.get(g)))
    # subjects (overlord key) without flag / giver, by colonial status
    for tag, cd in cb.items():
        if isinstance(cd, dict) and "overlord" in cd and has_val.get(tag):
            col = "colonial_parent" in cd
            g = has_tout[tag] > 0
            C[f"subject_{'colonial' if col else 'other'}_{'giver' if g else 'nongiver'}"] += 1
            if not col and not g: subj_nongiver_examples.setdefault(sid, []).append((tag, bool(flagged.get(tag))))
    # BEI details
    bd = cb.get("BEI")
    if isinstance(bd, dict) and has_val.get("BEI"):
        bei.append((sid, e["date"], has_val["BEI"], has_tout["BEI"], bd.get("overlord"), bd.get("transfer_trade_power_to"), bd.get("transfer_home_bonus")))
    tot.update(C)
    if not dup: dist.update(C)
for nm, c in (("ALL 86 entries", tot), ("84 DISTINCT", dist)):
    print("==", nm)
    for k in sorted(c): print(f"  {k}: {c[k]}")
for k, v in exc.items(): print("EXC", k, len(v), v[:14])
print("BEI per save (sid, date, entries_with_val, entries_with_tout, overlord, flag, transfer_home_bonus):")
for b in bei: print(" ", b)
print("non-colonial non-giver subjects: saves with any:", len(subj_nongiver_examples))
for sid in ("S14", "S42", "S80", "U03", "U05", "U06"):
    v = subj_nongiver_examples.get(sid, [])
    print(" ", sid, len(v), "with flag:", sum(1 for t, f in v if f), [t for t, f in v][:14])
