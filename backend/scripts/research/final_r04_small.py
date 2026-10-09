"""R04 final, script 6: in country-saves whose block has transfer_trade_power_to AND some t_out: does every entry with val carry t_out?
Behaviour at small val (the offset's origin / val<0.1 question)."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r04_common as F
import common
tot = Counter(); dist = Counter(); rows = []
for e in common.entries():
    sid = e["id"]; dup = sid in F.COPY_OF
    nodes = common.nodes(e)
    cb = common.block(e, "countries")
    gave = defaultdict(int)
    for n in nodes:
        for tag, c in F.entries_of(n).items():
            if "t_out" in c: gave[tag] += 1
    C = Counter()
    for n in nodes:
        for tag, c in F.entries_of(n).items():
            if tag in gave and "val" in c:
                v = F.m(c["val"])
                if "t_out" in c: C["giver_entries_with_val_and_tout"] += 1
                else:
                    C["giver_entries_with_val_no_tout"] += 1; rows.append((sid, n["definitions"], tag, v))
            if tag in gave and "val" not in c and "t_out" in c: C["tout_without_val"] += 1
            if tag in gave and "val" not in c and "t_in" in c: C["giver_tag_recv_entry"] += 1
    # all entries with val (any country) smallest values with/without t_out
    vals = sorted(F.m(c["val"]) for n in nodes for tag, c in F.entries_of(n).items() if "val" in c and F.m(c["val"]) > 0)
    C["entries_val_lt_1500"] += sum(1 for v in vals if v < 1500)
    tot.update(C)
    if not dup: dist.update(C)
print("ALL", dict(tot)); print("DISTINCT", dict(dist))
print("giver-tag entries with val but no t_out:", len(rows), "min/max val", (min(r[3] for r in rows), max(r[3] for r in rows)) if rows else None)
print(rows[:10])
