"""R06 final (2/4): the country-level merchant term R = 2 + 5*[reform] + 15*[trade_ideas >= 5]  over the played saves,
its absence in the 78 start snapshots, the threshold scan, and the +5 feature search (reforms, privileges, policies, modifiers, flags).
Independent code: raw save keys only.
"""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import final_r06_lib as L

saves = L.all_saves()
distinct = [(i, s) for i, s in saves if i not in L.COPIES]
snap = [(i, s) for i, s in distinct if i not in L.PLAYED]
played = [(i, s) for i, s in distinct if i in L.PLAYED]
REF = {"mercantilistic_approach_reform", "pious_merchants_reform"}


def modal_R(s):
    vals = defaultdict(list)
    for r in s["rows"]:
        if r["trader"]:
            vals[r["tag"]].append(round(L.residual(r), 1))
    return {t: Counter(v) for t, v in vals.items()}


def pred(c, thr=5):
    return 2.0 + 5.0 * bool(c["reforms"] & REF) + 15.0 * (c["ideas"].get("trade_ideas", 0) >= thr)


print("== formula vs observed, played saves (country-saves with a merchant entry)")
tot = ok = 0
excs = []
for i, s in played:
    for t, cnt in modal_R(s).items():
        tot += 1
        obs = cnt.most_common(1)[0][0]
        p = pred(s["c"][t])
        if abs(obs - p) < 0.05 and len(cnt) == 1:
            ok += 1
        else:
            excs.append((i, t, dict(cnt), p))
    print(" ", i, "done")
print("country-saves", tot, "formula exact (single-valued and equal)", ok, "exceptions", len(excs))
for e in sorted(excs):
    print("  EXC", e)
# same per save
per = Counter(); perok = Counter()
for i, s in played:
    for t, cnt in modal_R(s).items():
        per[i] += 1
        if len(cnt) == 1 and abs(cnt.most_common(1)[0][0] - pred(s["c"][t])) < 0.05:
            perok[i] += 1
print("per save: ", {i: (perok[i], per[i]) for i in per})

print("\n== threshold scan for trade_ideas level (country-saves, modal R)")
for thr in range(1, 9):
    good = 0
    for i, s in played:
        for t, cnt in modal_R(s).items():
            if abs(cnt.most_common(1)[0][0] - pred(s["c"][t], thr)) < 0.05:
                good += 1
    print("  thr", thr, good, "of", tot)
lv = defaultdict(Counter)
for i, s in played:
    for t, cnt in modal_R(s).items():
        obs = cnt.most_common(1)[0][0]
        lv[int(s["c"][t]["ideas"].get("trade_ideas", 0))][obs] += 1
print("  trade_ideas level -> R counts:")
for k in sorted(lv):
    print("   ", k, dict(lv[k]))

print("\n== snapshots: merchant country-saves, predicted R>0 vs observed")
n = pos = obsnz = 0
pred_c = Counter()
for i, s in snap:
    for t, cnt in modal_R(s).items():
        n += 1
        p = pred(s["c"][t])
        pred_c[p] += 1
        if p > 0:
            pos += 1
        if any(abs(v) > 0.05 for v in cnt):
            obsnz += 1
            print("  SNAPSHOT NONZERO", i, t, dict(cnt))
print("  merchant country-saves in 78 snapshots", n, "predicted R>0", pos, "(by value", dict(pred_c), ") observed R != 0:", obsnz)
# snapshot merchant entries count
print("  snapshot merchant entries", sum(1 for _, s in snap for r in s["rows"] if r["trader"]))

print("\n== +5 feature search: played country-saves, residual beyond 2 + 15*[trade_ideas>=5]")
feat_pos = Counter(); feat_neg = Counter(); npos = nneg = 0
members = []
for i, s in played:
    for t, cnt in modal_R(s).items():
        obs = cnt.most_common(1)[0][0]
        base = 2.0 + 15.0 * (s["c"][t]["ideas"].get("trade_ideas", 0) >= 5)
        d = obs - base
        c = s["c"][t]
        feats = {("reform", x) for x in c["reforms"]} | {("priv", x) for x in c["privs"]} | {("policy", x) for x in c["policies"]} | \
                {("mod", x) for x in c["mods"]} | {("flag", x) for x in c["flags"]} | {("govt", c["govt"]), ("tg", c["tg"]), ("rel", c["rel"])} | \
                {("idea", g, int(v)) for g, v in c["ideas"].items()}
        if abs(d - 5.0) < 0.05:
            npos += 1; feat_pos.update(feats); members.append((i, t))
        elif abs(d) < 0.05:
            nneg += 1; feat_neg.update(feats)
print("  +5 country-saves", npos, "0 country-saves", nneg)
rows = []
for f, c in feat_pos.items():
    rows.append((c / npos, feat_neg[f], c, f))
rows.sort(key=lambda x: (-x[2], x[1]))
print("  features present in the +5 group, by count (count_in_+5, count_in_0):")
for frac, neg, c, f in rows[:14]:
    print("   ", f, c, neg)
# features with zero false positives
clean = [(c, f) for frac, neg, c, f in rows if neg == 0 and c >= 3]
clean.sort(reverse=True)
print("  features with 0 false positives (count>=3):", clean[:12])
print("  members not covered by the 2 reforms:", [m for m in members if not (saves and [s for i, s in played if i == m[0]][0]["c"][m[1]]["reforms"] & REF)])
cover = sum(1 for m in members if [s for i, s in played if i == m[0]][0]["c"][m[1]]["reforms"] & REF)
print("  covered by mercantilistic/pious reform:", cover, "of", npos)
fa = Counter(); fb = Counter()
for i, s in played:
    for t, cnt in modal_R(s).items():
        c = s["c"][t]
        obs = cnt.most_common(1)[0][0]
        d = obs - (2.0 + 15.0 * (c["ideas"].get("trade_ideas", 0) >= 5))
        for r in REF:
            if r in c["reforms"]:
                fa[(r, round(d, 1))] += 1
        if "free_trade_reform" in c["reforms"]:
            fb[round(d, 1)] += 1
print("  reform -> residual beyond 2+15*ideas:", dict(fa))
print("  free_trade_reform -> same residual:", dict(fb))
