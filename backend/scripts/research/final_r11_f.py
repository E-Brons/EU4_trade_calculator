"""R11 final (2/5): what sets f = ship_power / sum(base). National idea groups (leaderless fleets), leader maneuver (leader fleets),
luck=yes, over S79, S80, U03, U04, U05, U06 (copies U01/U02 excluded). Independent code, no prior on f."""
import sys
sys.path.insert(0, "scripts/research")
import final_r11_lib as L
from collections import Counter, defaultdict

rows = []
for s in L.saves():
    if not L.has_ships(s): continue
    for r in L.reconcile(s):
        if r["f"] is None: continue
        key = r["key"]; tag = key[0]
        # fleets that are counted in every fit (the fit is the same f for all; use union-intersection)
        subs = [set(x[0]) for x in r["fits"]]
        counted = set.intersection(*subs)
        possible = set.union(*subs)
        leaders = [r["fleets"][i]["leader"] for i in possible if r["fleets"][i]["leader"]]
        status = "noleader" if not leaders else ("leader" if all(r["fleets"][i]["leader"] for i in counted) and counted == possible else "mixed")
        c = s.countries[tag]
        ls = L.leader_stats(c)
        man = sorted({ls.get(l["id"], {}).get("maneuver") for l in leaders})
        groups = c.get("active_idea_groups")
        rows.append(dict(save=s.id, tag=tag, node=key[1], f=r["f"], status=status, man=man, n=r["n"],
                         groups=sorted(groups) if isinstance(groups, dict) else [], luck=c.get("luck"),
                         nfleets=len(r["fleets"]), ncounted=len(possible)))
print("entries with f:", len(rows), dict(Counter(r["save"] for r in rows)))
print("f histogram:", dict(sorted(Counter(r["f"] for r in rows).items())))
print("status:", dict(Counter(r["status"] for r in rows)))
print("TUR f values:", dict(Counter(r["f"] for r in rows if r["tag"] == "TUR")), "n TUR", sum(1 for r in rows if r["tag"] == "TUR"))
print("--- entries whose counted fleets include a leader")
for r in rows:
    if r["status"] != "noleader": print("  ", r["save"], r["tag"], r["node"], "f", r["f"], r["status"], "maneuver", r["man"], "ships", r["n"], "fleets", r["ncounted"])

# leader stats vs f: full stats of the leaders
print("--- leader stat table (fire shock maneuver siege) for leader entries")
seen = set()
for s in L.saves():
    if not L.has_ships(s): continue
    for r in L.reconcile(s):
        if r["f"] is None: continue
        subs = [set(x[0]) for x in r["fits"]]
        for i in set.union(*subs):
            ld = r["fleets"][i]["leader"]
            if ld:
                st = L.leader_stats(s.countries[r["key"][0]]).get(ld["id"], {})
                k = (s.id, r["key"], ld["id"])
                if k in seen: continue
                seen.add(k)
                print("  ", s.id, r["key"], "leader", ld["id"], {x: st.get(x) for x in ("fire", "shock", "maneuver", "siege")}, "f", r["f"], "(f-1)/maneuver =", (round((r["f"] - 1) / st["maneuver"], 4) if st.get("maneuver") else None))

# leaderless (save, country) pairs
pairs = defaultdict(list)
for r in rows:
    if r["status"] == "noleader": pairs[(r["save"], r["tag"])].append(r)
print("leaderless (save,country) pairs:", len(pairs), " pairs with >1 distinct f:", sum(1 for v in pairs.values() if len({x["f"] for x in v}) > 1))
nz = {k: v for k, v in pairs.items() if any(x["f"] != 1.0 for x in v)}
print("leaderless pairs with f != 1:", len(nz))
for k, v in sorted(nz.items()): print("  ", k, sorted({x["f"] for x in v}), [x["node"] for x in v], [g for g in v[0]["groups"] if g.endswith("_ideas")][-3:])
gf = defaultdict(Counter)
for k, v in pairs.items():
    f = v[0]["f"] if len({x["f"] for x in v}) == 1 else "mixed"
    for g in v[0]["groups"]: gf[g][f] += 1
print("idea groups seen in any leaderless pair with f != 1:")
for g, c in sorted(gf.items()):
    if any(f != 1.0 for f in c): print("  ", g, dict(c))
three = ("fijian_ideas", "luzon_ideas", "samoan_ideas")
print("f=1 leaderless pairs carrying one of the three groups:", sum(c.get(1.0, 0) for g, c in gf.items() if g in three))
print("f != 1 leaderless pairs NOT carrying one of the three:", [k for k, v in nz.items() if not set(v[0]["groups"]) & set(three)])
# other national groups: list of groups seen with f == 1 only, and whether they occur in >=1 pair
nat = {g: dict(c) for g, c in gf.items() if g.endswith("_ideas") and g not in three}
print("distinct idea groups in leaderless pairs:", len(gf), " of which occur only with f=1:", sum(1 for g, c in gf.items() if set(c) == {1.0}))
for g in ("hawaiian_ideas", "chinese_ideas", "swahili_ideas", "maori_ideas", "defensive_ideas"):
    print("   ", g, dict(gf.get(g, {})))
# luck
lucky = [(k, v[0]["f"]) for k, v in pairs.items() if v[0]["luck"] in (True, "yes")]
print("lucky leaderless pairs:", len(lucky), " with f != 1:", sum(1 for _, f in lucky if f != 1.0))
print("lucky tags per save:", {s.id: sorted(t for t, c in s.countries.items() if isinstance(c, dict) and c.get("luck") in (True, "yes")) for s in L.saves() if L.has_ships(s)})
# same tag & node, with/without leader (HOL english_channel), DAN, SPA
print("--- same (tag,node) across saves")
for tag, node in (("HOL", "english_channel"), ("DAN", "lubeck"), ("SPA", "ivory_coast"), ("MOR", "ivory_coast")):
    print("  ", tag, node, [(r["save"], r["f"], r["status"], r["man"], r["n"]) for r in rows if r["tag"] == tag and r["node"] == node])
print("  DAN:", [(r["save"], r["node"], r["f"], r["status"]) for r in rows if r["tag"] == "DAN"])
print("  SPA:", [(r["save"], r["node"], r["f"], r["status"], r["man"]) for r in rows if r["tag"] == "SPA"])
# per-country constancy across leaderless entries in the same save
print("leaderless (save, country) pairs where f is constant:", sum(1 for v in pairs.values() if len({x["f"] for x in v}) == 1), "of", len(pairs))
