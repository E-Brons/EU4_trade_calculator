"""R11 final (1/5): storage and fleet-to-entry reconciliation, counted / uncounted fleets, limits, non-light types.

Independent of ver2_r11_*.py / r11_r14_*.py / u345_*: fresh subset enumeration, no prior on f.
"""
import sys, itertools
sys.path.insert(0, "scripts/research")
import final_r11_lib as L
from collections import Counter, defaultdict

BASE = L.BASE
tot = Counter()
rows_f = []            # (save, tag, node, f, n_light)
amb_list, nofit_list = [], []
uncounted = []         # (save, tag, node, name, omw, has_path)
counted_omw = Counter(); uncounted_omw = Counter()
nps_rows = []
caps = []
morale = []; strength_n = 0; ships_total = 0
nonlight_rows = []
inland_entries = 0; inland_fleets = 0
ships_without_mission_in_entries = 0
ship_entries_wo_fleet = []
per_save = {}
sum_entry_power_fleet = 0

for s in L.saves():
    if not L.has_ships(s):
        tot["start_saves_without_ship_entries"] += 1
        # also: no fleet has a protect mission in these saves
        tot["fleets_with_mission_in_noship_saves"] += len(s.fleets())
        continue
    fl = defaultdict(list)
    for f in s.fleets():
        fl[(f["tag"], f["node"])].append(f)
    ents = {k: c for k, c in s.ent.items() if "light_ship" in c or "ship_power" in c}
    # (a) key consistency
    for k, c in ents.items():
        if ("light_ship" in c) != ("ship_power" in c):
            tot["entries_with_only_one_of_light_ship_ship_power"] += 1
        if k[1] in L.INLAND: inland_entries += 1
    for f in s.fleets():
        if f["node"] in L.INLAND: inland_fleets += 1
    nf = len(s.fleets()); tot["fleets"] += nf; tot["entries"] += len(ents)
    per_save[s.id] = [len(ents), nf]
    counted_fleet_ids = set(); uncounted_fleet_ids = set(); undecided = set()
    for key in set(fl) | set(ents):
        fleets = fl.get(key, [])
        c = ents.get(key)
        if c is None or int(L.fnum(c.get("light_ship"))) == 0:
            # fleets at a node where the entry has no light_ship: all uncounted (if they hold light ships)
            for i, f in enumerate(fleets):
                if sum(f["light"].values()) > 0: uncounted_fleet_ids.add((key, i))
            if c is not None and L.fnum(c.get("ship_power")) != 0:
                tot["entry_ship_power_without_light_ship"] += 1
            continue
        n_e, sp_e = int(c["light_ship"]), L.fnum(c["ship_power"])
        if not fleets:
            ship_entries_wo_fleet.append((s.id, key)); continue
        if len(fleets) > 20: raise SystemExit("too many fleets " + str((s.id, key)))
        fits = []
        idx = [i for i, f in enumerate(fleets) if sum(f["light"].values()) > 0]
        for r in range(1, len(idx) + 1):
            for sub in itertools.combinations(idx, r):
                n = sum(sum(fleets[i]["light"].values()) for i in sub)
                if n != n_e: continue
                b = sum(BASE[t] * k for i in sub for t, k in fleets[i]["light"].items())
                fits.append((sub, b, sp_e / b))
        if not fits:
            nofit_list.append((s.id, key, n_e, sp_e)); continue
        fs = {round(x[2], 4) for x in fits}
        if len(fs) > 1:
            amb_list.append((s.id, key, n_e, sp_e, sorted(fs))); continue
        f = fs.pop()
        rows_f.append((s.id, key[0], key[1], f, n_e, sp_e, round(fits[0][1], 3), len(fits)))
        if len(fits) == 1:
            sub = fits[0][0]
            for i in idx:
                (counted_fleet_ids if i in sub else uncounted_fleet_ids).add((key, i))
        else:
            # several subsets with the same f: fleets in all subsets are counted, in none uncounted, else undecided
            allsub = [set(x[0]) for x in fits]
            for i in idx:
                if all(i in a for a in allsub): counted_fleet_ids.add((key, i))
                elif not any(i in a for a in allsub): uncounted_fleet_ids.add((key, i))
                else: undecided.add((key, i))
            tot["entries_with_multiple_subsets_same_f"] += 1
    # fleet-level stats
    for key, fleets in fl.items():
        for i, f in enumerate(fleets):
            if sum(f["light"].values()) == 0:
                tot["protect_fleets_without_light_ships"] += 1; continue
            st = (key, i)
            o = str(f["omw"])
            if st in counted_fleet_ids:
                counted_omw[o] += 1
                for sh in f["ships"]:
                    if sh.get("type") in BASE:
                        morale.append(L.fnum(sh.get("morale"))); ships_total += 1
                        if "strength" in sh: strength_n += 1
            elif st in uncounted_fleet_ids:
                uncounted_omw[o] += 1
                uncounted.append((s.id, key[0], key[1], f["name"], o, "path" in f["raw"], f["raw"].get("movement_progress"), f["pm"].get("current_cycle_begin"), f["fid"]))
            elif st in undecided:
                tot["undecided_fleets"] += 1
                uncounted.append((s.id, key[0], key[1], f["name"], "UNDECIDED:" + o, "path" in f["raw"], f["raw"].get("movement_progress"), f["pm"].get("current_cycle_begin"), f["fid"]))
            if f["other"]:
                nonlight_rows.append((s.id, key, dict(f["light"]), dict(f["other"])))
    # nps
    for tag, c in s.countries.items():
        if not isinstance(c, dict) or "num_ships_protecting_trade" not in c: continue
        nps = int(L.fnum(c["num_ships_protecting_trade"]))
        on_mis = sum(sum(f["light"].values()) for f in s.fleets() if f["tag"] == tag)
        in_ent = sum(int(L.fnum(e.get("light_ship"))) for (t, n), e in s.ent.items() if t == tag)
        if nps == 0 and on_mis == 0 and in_ent == 0: continue
        nps_rows.append((s.id, tag, nps, in_ent, on_mis))
    caps.append((max((int(L.fnum(c.get("light_ship"))) for c in ents.values()), default=0), s.id,
                 max(ents, key=lambda k: int(L.fnum(ents[k].get("light_ship"))))))

print("saves with ship entries:", per_save)
print("TOTAL", dict(tot))
print("entries fitted (unique f):", len(rows_f), " ambiguous f:", amb_list, " no fit:", nofit_list, " entries w/o any fleet:", ship_entries_wo_fleet)
print("f histogram:", dict(sorted(Counter(r[3] for r in rows_f).items())), " min f:", min(r[3] for r in rows_f))
print("per-save fitted entries:", dict(Counter(r[0] for r in rows_f)))
print("entries with f != 1:")
for r in rows_f:
    if r[3] != 1.0: print("   ", r)
print("TUR entries:", [(r[0], r[2], r[4], r[5], r[3]) for r in rows_f if r[1] == "TUR"])
print("entries with several equivalent subsets:", [r for r in rows_f if r[7] > 1])
print("inland entries:", inland_entries, " inland protect fleets:", inland_fleets)
print("counted fleets on_my_way:", dict(counted_omw), " uncounted fleets on_my_way:", dict(uncounted_omw))
print("uncounted fleets:")
for u in uncounted: print("   ", u)
print("light ships of counted fleets: n", ships_total, "morale min/max", min(morale), max(morale), " with strength key:", strength_n)
nb = Counter();
for sid, key, lt, ot in nonlight_rows: nb[tuple(sorted(ot))] += 1
print("protect fleets carrying non-light ships (fleet count by type set):", dict(nb))
ne = [(sid, key, lt, ot) for sid, key, lt, ot in nonlight_rows]
print("   examples:", ne[:5], "total", len(ne))
print("largest entries:", sorted(caps, reverse=True)[:6])
# nps summary
same_mis = sum(1 for r in nps_rows if r[2] == r[4]); same_ent = sum(1 for r in nps_rows if r[2] == r[3])
print("num_ships_protecting_trade rows:", len(nps_rows), " nps==on missions:", same_mis, " nps==sum entries light_ship:", same_ent)
print("  nps != on missions:", [r for r in nps_rows if r[2] != r[4]])
print("  nps != sum(entries):", [r for r in nps_rows if r[2] != r[3]])

# ---- follow fleets by id across saves (state transitions) and detail of the no-fit entries
print("=== fleet id tracking for uncounted fleets with key / transitions")
track = defaultdict(dict)   # fid -> save -> (counted?/uncounted, omw)
for s in L.saves():
    if not L.has_ships(s): continue
    fl = defaultdict(list)
    for f in s.fleets(): fl[(f["tag"], f["node"])].append(f)
    for key, fleets in fl.items():
        c = s.ent.get(key)
        n_e = int(L.fnum(c.get("light_ship"))) if c else 0
        for f in fleets:
            track[f["fid"]][s.id] = (key, str(f["omw"]), sum(f["light"].values()), n_e)
for fid in (403526, 46171, 39897, 39906, 352002, 39728):
    print(fid, track.get(fid))

# ---- index base of protect_mission.node: entries whose light_ship is reproduced by some subset of fleets, for offsets -1, 0, +1
print("=== node index base test (entries reproduced by a fleet subset, by offset added to the stored index; 1-based means offset 0 = order[idx-1])")
for off in (-1, 0, 1, 2):
    ok = n_e_tot = 0
    for s in L.saves():
        if not L.has_ships(s): continue
        fl = defaultdict(list)
        for f in s.fleets():
            j = f["nodeidx"] - 1 + off
            if 0 <= j < len(s.order): fl[(f["tag"], s.order[j])].append(sum(f["light"].values()))
        for key, c in s.ent.items():
            if "light_ship" not in c: continue
            n_e_tot += 1
            cnts = fl.get(key, []); n = int(c["light_ship"])
            if any(sum(sub) == n for r in range(1, len(cnts) + 1) for sub in itertools.combinations(cnts, r)): ok += 1
    print("  offset", off, "entries reproduced", ok, "of", n_e_tot)
