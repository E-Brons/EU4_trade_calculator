"""R06 final (1/4): whole-corpus decomposition  extras = 5*has_capital + sum(modifier.power) + R*[has_trader].

Prints: (a) counts, (b) class table, (c) residual outside the played saves, (d) entry-level reproduction with every exception,
(e) R by class and constancy per country-save, (f) modifiers census, (g) recalled, (h) entries without has_trader with residual.
Independent code: raw save keys only.
"""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r06_lib as L

saves = L.all_saves()
distinct = [(i, s) for i, s in saves if i not in L.COPIES]
print("entries", len(saves), "distinct", len(distinct))
snap = [(i, s) for i, s in distinct if i not in L.PLAYED]
played = [(i, s) for i, s in distinct if i in L.PLAYED]
print("snapshot saves", len(snap), "played distinct", len(played), [i for i, _ in played])

n_all = sum(len(s["rows"]) for _, s in saves)
n_dist = sum(len(s["rows"]) for _, s in distinct)
print("rows with max_pow: all entries", n_all, "distinct saves", n_dist)

# (b) class table over the 86 entries (as response_1) and distinct
for label, grp in (("86 entries", saves), ("84 distinct", distinct)):
    tab = defaultdict(Counter)
    for _, s in grp:
        for r in s["rows"]:
            tab[L.klass(r)][round(L.extras(r), 1)] += 1
    print("\nextras by class,", label)
    for k in ("home", "home+merchant", "collect-away+merchant", "collect-away", "steer+merchant", "steer", "passive", "passive+merchant"):
        c = tab.get(k, Counter()); print(" ", k, sum(c.values()), c.most_common(12))

# (c) residual outside played saves
nz = 0; tot = 0; mer = 0; maxdev = 0.0
for _, s in snap:
    for r in s["rows"]:
        tot += 1
        mer += r["trader"]
        res = L.residual(r)
        maxdev = max(maxdev, abs(res))
        if abs(res) > L.TOL:
            nz += 1; print("  SNAPSHOT NONZERO", r["sid"], r["node"], r["tag"], round(res, 3))
print("\nsnapshots: entries", tot, "with has_trader", mer, "non-zero residual", nz, "max |residual|", round(maxdev, 4))
# snapshot entries with modifiers
cm = Counter()
for _, s in snap:
    for r in s["rows"]:
        for k, p, pm, d in r["mods"]:
            cm[(k, p)] += 1
print("snapshot modifier blocks", dict(cm))

# (d) entry-level reproduction, played saves, with the country-level R (median of the country-save's entries with trader)
def cs_R(s):
    vals = defaultdict(list)
    for r in s["rows"]:
        if r["trader"]:
            vals[r["tag"]].append(round(L.residual(r), 1))
    return vals
tot = 0; ok = 0; exc = []
for i, s in played:
    vals = cs_R(s)
    for r in s["rows"]:
        tot += 1
        if r["trader"]:
            v = Counter(vals[r["tag"]]).most_common(1)[0][0]
        else:
            v = 0.0
        if abs(L.residual(r) - v) <= L.TOL:
            ok += 1
        else:
            exc.append((i, r["tag"], r["node"], round(L.residual(r), 3), v, L.klass(r)))
print("\nplayed saves (distinct, 6): entries", tot, "reproduced with R=country-save modal value", ok, "exceptions", len(exc))
for e in exc:
    print("  EXC", e)

# (e) R by class (played), constancy per country-save
byclass = defaultdict(Counter)
single = 0; multi = []
R_of = {}
for i, s in played:
    vals = cs_R(s)
    for t, v in vals.items():
        c = Counter(v)
        if any(x != 0.0 for x in c):
            if len(c) == 1:
                single += 1
            else:
                multi.append((i, t, dict(c)))
            R_of[(i, t)] = c.most_common(1)[0][0]
    for r in s["rows"]:
        if r["trader"]:
            byclass[L.klass(r)][round(L.residual(r), 1)] += 1
print("\nnon-zero-R country-saves (distinct played, 6 saves):", single + len(multi), "single-valued", single, "multi-valued", multi)
print("values of R per country-save:", Counter(R_of.values()))
for k, c in byclass.items():
    print("  class", k, sum(c.values()), dict(c))
# all merchant country-saves, incl zero
allcs = sum(len(cs_R(s)) for _, s in played)
print("merchant country-saves in played distinct saves", allcs, "with R == 0:", allcs - len(R_of))

# (f) modifiers census over all distinct saves
cen = defaultdict(Counter); cls = defaultdict(Counter); pmod = Counter(); dur = defaultdict(list)
for i, s in distinct:
    for r in s["rows"]:
        for k, p, pm, d in r["mods"]:
            cen[k][p] += 1; cls[k][L.klass(r)] += 1; pmod[pm] += 1
            if d is not None: dur[k].append(d)
print("\nmodifier census (distinct saves): key -> power counts; classes; duration range")
for k in sorted(cen):
    print(" ", k, dict(cen[k]), dict(cls[k]), (min(dur[k]), max(dur[k])) if dur[k] else None)
print("power_modifier values", dict(pmod))

# (g) which saves contain which modifier keys
where = defaultdict(set)
for i, s in distinct:
    for r in s["rows"]:
        for k, p, pm, d in r["mods"]:
            where[k].add(i)
for k, v in where.items():
    print(" keys in saves:", k, "snapshots" if any(x not in L.PLAYED for x in v) else "played only", len(v), sorted(v)[:12])

# (h) entries without has_trader with non-zero residual (all distinct)
print("\nentries without has_trader and residual != 0:")
c = 0
for i, s in saves:
    for r in s["rows"]:
        if not r["trader"] and abs(L.residual(r)) > L.TOL:
            c += 1; print("  ", i, r["tag"], r["node"], L.klass(r), round(L.extras(r), 3), round(L.residual(r), 3), [m[:2] for m in r["mods"]])
print("count (86 entries)", c)
