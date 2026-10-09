"""R06 final (3/4): per-entry classification of the played saves against  extras = 5*has_capital + R(country-save)*[has_trader] + applied modifiers.
R(country-save) = most common residual (extras - 5*cap - modifier powers) among the country's merchant entries of that save.
Classes: consistent (E == sum of listed modifier powers), listed-not-applied (E == 0 but a modifier is listed), other (printed).
Also: merchant_recalled rows ordered by `duration` (initial duration inferred from the maximum seen) against the save date.
Independent code: raw save keys only.
"""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r06_lib as L

saves = L.all_saves()
distinct = [(i, s) for i, s in saves if i not in L.COPIES]
played = [(i, s) for i, s in distinct if i in L.PLAYED]


def modal_R(s):
    d = defaultdict(list)
    for r in s["rows"]:
        if r["trader"]:
            d[r["tag"]].append(round(L.residual(r), 1))
    return {t: Counter(v).most_common(1)[0][0] for t, v in d.items()}


tot = Counter(); listed_na = []; other = []
for i, s in played:
    R = modal_R(s)
    for r in s["rows"]:
        E = L.extras(r) - 5.0 * r["cap"] - (R.get(r["tag"], 0.0) if r["trader"] else 0.0)
        M = L.mod_sum(r)
        if abs(E - M) <= L.TOL:
            tot["consistent"] += 1
            if r["mods"]:
                tot["consistent with modifier listed"] += 1
        elif abs(E) <= L.TOL and r["mods"]:
            tot["listed-not-applied"] += 1; listed_na.append((i, s["date"], r["tag"], r["node"], r["mods"]))
        else:
            tot["other"] += 1; other.append((i, s["date"], r["tag"], r["node"], L.klass(r), round(E, 3), r["mods"]))
print("played-save entries (6 distinct saves):", sum(tot[k] for k in ("consistent", "listed-not-applied", "other")), dict(tot))
print("listed-not-applied:")
for x in listed_na:
    print("  ", x)
print("other (listed-not-applied excluded):")
for x in other:
    print("  ", x)

print("\nmerchant_recalled rows, by duration (desc): save, date, tag, node, duration, applied?")
rows = []
for i, s in played:
    R = modal_R(s)
    for r in s["rows"]:
        for k, p, pm, d in r["mods"]:
            if k == "merchant_recalled":
                E = L.extras(r) - 5.0 * r["cap"] - (R.get(r["tag"], 0.0) if r["trader"] else 0.0)
                others = sum(pp for kk, pp, _, _ in r["mods"] if kk != "merchant_recalled")
                applied = abs(E - others - p) <= L.TOL
                notapp = abs(E - others) <= L.TOL
                rows.append((d, i, s["date"], r["tag"], r["node"], "applied" if applied else ("NOT applied" if notapp else "?")))
rows.sort(reverse=True)
print("  recalled rows", len(rows), "applied", sum(1 for x in rows if x[-1] == "applied"), "not applied", sum(1 for x in rows if x[-1] == "NOT applied"), "unclassified", sum(1 for x in rows if x[-1] == "?"))
for x in rows[:8]:
    print("  ", x)
print("  durations:", "max", rows[0][0], "second-highest applied:", max(d for d, *_, a in rows if a == "applied"))

# expired candidates: entries with E != 0 and no listed modifier that explains it
print("\nentries with E != 0 and no modifier listed (candidate 'modifier expired after max_pow was computed'):")
for i, s in played:
    R = modal_R(s)
    for r in s["rows"]:
        E = L.extras(r) - 5.0 * r["cap"] - (R.get(r["tag"], 0.0) if r["trader"] else 0.0)
        if abs(E) > L.TOL and not r["mods"]:
            print("  ", i, s["date"], r["tag"], r["node"], L.klass(r), round(E, 3))
