"""R11 final (extra): per-type base trade power recovered from the data (pure-type entries, no project constants), types in counted fleets,
multi-entry leaderless pairs, and the predictive rule for f."""
import sys, statistics
sys.path.insert(0, "scripts/research")
import final_r11_lib as L
from collections import Counter, defaultdict

pure = defaultdict(Counter)       # type -> Counter(round(sp/n,3))
types_counted = Counter()
pairs_entries = defaultdict(list)
pred_ok = pred_n = 0
three = {"fijian_ideas": 1.1, "luzon_ideas": 1.1, "samoan_ideas": 1.2}
for s in L.saves():
    if not L.has_ships(s): continue
    for r in L.reconcile(s):
        if not r["fits"] or r["f"] is None: continue
        subs = [set(x[0]) for x in r["fits"]]
        counted = set.intersection(*subs)
        comp = Counter()
        for i in counted:
            for t, k in r["fleets"][i]["light"].items(): comp[t] += k
        for t, k in comp.items(): types_counted[t] += k
        if len(comp) == 1 and counted == set.union(*subs):
            t = next(iter(comp)); pure[t][round(r["sp"] / r["n"], 3)] += 1
        leader = any(r["fleets"][i]["leader"] for i in counted)
        if not leader:
            pairs_entries[(s.id, r["key"][0])].append(r["f"])
            groups = s.countries[r["key"][0]].get("active_idea_groups") or {}
            pred = max([three[g] for g in groups if g in three], default=1.0)
            pred_n += 1; pred_ok += abs(pred - r["f"]) < 1e-9
print("pure-type entries: value of ship_power/light_ship per type (value: entries)")
for t, c in sorted(pure.items()): print("  ", t, dict(c.most_common(6)), " total entries", sum(c.values()))
print("light ships in counted fleets by type:", dict(types_counted))
multi = [k for k, v in pairs_entries.items() if len(v) >= 2]
print("leaderless (save,country) pairs:", len(pairs_entries), " with >=2 entries:", len(multi), " f constant in those:", sum(len(set(pairs_entries[k])) == 1 for k in multi))
print("predictive rule f = {fijian 1.1, luzon 1.1, samoan 1.2, else 1.0} on leaderless entries:", pred_ok, "of", pred_n)

# ---- entries containing damaged ships (ship has a `strength` key) and the copy check
dam_n = dam_f1 = 0
for s in L.saves():
    if not L.has_ships(s): continue
    for r in L.reconcile(s):
        if not r["fits"] or r["f"] is None: continue
        counted = set.intersection(*[set(x[0]) for x in r["fits"]])
        if any("strength" in sh for i in counted for sh in r["fleets"][i]["ships"] if sh.get("type") in L.BASE):
            dam_n += 1; dam_f1 += abs(r["f"] - 1.0) < 1e-9
print("entries whose counted fleets contain a ship with a `strength` key:", dam_n, " of which f == 1.0:", dam_f1, "(the rest:", dam_n - dam_f1, "are the f != 1 entries)")
es = {e["id"]: e for e in L.common.entries()}
for cp, orig in L.COPIES.items():
    a, b = L.Save(es[cp]), L.Save(es[orig])
    ea = {k: v for k, v in a.ent.items() if "light_ship" in v}; eb = {k: v for k, v in b.ent.items() if "light_ship" in v}
    print("copy", cp, "==", orig, ": ship entries equal:", ea == eb, len(ea), " trade nodes equal:", a.nodes == b.nodes)

ratios = [L.fnum(c["ship_power"]) / int(L.fnum(c["light_ship"])) for s in L.saves() if L.has_ships(s) for c in s.ent.values() if "light_ship" in c and int(L.fnum(c["light_ship"])) > 0]
print("ship_power / light_ship over", len(ratios), "entries: min %.3f median %.3f max %.3f" % (min(ratios), statistics.median(ratios), max(ratios)))
