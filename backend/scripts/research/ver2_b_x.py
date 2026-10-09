"""Independent check of the R07 numbers: TUR X series, away-minus-home pairs, YEM, the strict 'nothing visible changed' subset."""
import sys
from collections import Counter
sys.path.insert(0, ".")
import ver2_b_lib as L

PLAYED = ["S79", "S80", "U03", "U04", "U05"]
data = dict(L.saves(set(PLAYED)))


def X(e):
    return e["money"] / e["total"] - 1 if e["total"] and e["money"] is not None else None


def home_x(s, tag, min_total=3.0):
    h = L.home_node(s, tag)
    if h is None:
        return None
    e = s["nodes"][h]["e"][tag]
    if not e["collect"] or e["total"] is None or e["total"] < min_total:
        return None
    return X(e), e["trader"]


def away_xs(s, tag, min_total=3.0):
    out = []
    for nid, n in s["nodes"].items():
        e = n["e"].get(tag)
        if e and e["trader"] and e["collect"] and not e["cap"] and e["total"] and e["total"] >= min_total:
            out.append(X(e))
    return out


print("TUR X (home / away values at 3 decimals):")
for sid in PLAYED:
    s = data[sid]
    hx = home_x(s, "TUR", 1.0)
    ax = away_xs(s, "TUR", 1.0)
    print(f"  {sid}: home X={hx[0]:.4f} (merchant {hx[1]})  away X={[round(a, 4) for a in ax]}")

print()
print("pairs away X - home X (min total 3), by home merchant:")
for sid in PLAYED:
    s = data[sid]
    cnt = Counter()
    for tag in s["c"]:
        hx = home_x(s, tag)
        ax = away_xs(s, tag)
        if hx is None or not ax:
            continue
        d = sorted(ax)[len(ax) // 2] - hx[0]
        cnt[("home merchant" if hx[1] else "home no merchant", round(d, 2) + 0.0)] += 1
    print(f"  {sid}: {dict(sorted(cnt.items()))}")

print()
U04, U05, U03 = data["U04"], data["U05"], data["U03"]
for tag in ("YEM", "TUR"):
    for a, b in (("U04", "U05"),):
        A, B = data[a], data[b]
        ha, hb = home_x(A, tag, 1.0), home_x(B, tag, 1.0)
        ca, cb = A["c"][tag], B["c"][tag]
        print(f"{tag} {a}->{b}: home node {L.home_node(A, tag)} X {ha[0]:.3f}(merchant {ha[1]}) -> {hb[0]:.3f}(merchant {hb[1]}) | ideas same {ca['ideas']==cb['ideas']} reforms same {ca['reforms']==cb['reforms']} tech {ca['tech']} -> {cb['tech']} n60 {ca['n60']} -> {cb['n60']} estates {ca['estates']} -> {cb['estates']} | modifiers +{sorted(cb['modkeys']-ca['modkeys'])} -{sorted(ca['modkeys']-cb['modkeys'])}")


def strict(a, b, min_total):
    A, B = data[a], data[b]
    cands, nonzero = [], []
    for tag in A["c"]:
        if tag not in B["c"]:
            continue
        ha, hb = home_x(A, tag, min_total), home_x(B, tag, min_total)
        if ha is None or hb is None:
            continue
        ca, cb = A["c"][tag], B["c"][tag]
        same = (ha[1] == hb[1] and ca["n60"] == cb["n60"] and ca["tech"][1] == cb["tech"][1] and ca["ideas"] == cb["ideas"]
                and ca["reforms"] == cb["reforms"] and ca["modkeys"] == cb["modkeys"])
        cands.append(tag)
        if same:
            d = hb[0] - ha[0]
            nonzero.append((tag, round(d, 3))) if abs(d) > 0.0015 else None
    return len(cands), nonzero


for a, b in (("U03", "U04"), ("U04", "U05")):
    for mt in (3.0, 1.0):
        n, nz = strict(a, b, mt)
        # count strict-unchanged separately
        A, B = data[a], data[b]
        su = 0
        for tag in A["c"]:
            if tag not in B["c"]: continue
            ha, hb = home_x(A, tag, mt), home_x(B, tag, mt)
            if ha is None or hb is None: continue
            ca, cb = A["c"][tag], B["c"][tag]
            if (ha[1] == hb[1] and ca["n60"] == cb["n60"] and ca["tech"][1] == cb["tech"][1] and ca["ideas"] == cb["ideas"] and ca["reforms"] == cb["reforms"] and ca["modkeys"] == cb["modkeys"]):
                su += 1
        print(f"strict subset {a}->{b} (home X measurable with total>={mt}): home-X countries in both {n}; nothing visible changed {su}; of these dX != 0: {len(nz)} {nz}")

print()
print("estate hypothesis counter-cases (n60 change, merchant same, dX):")
for a, b in (("U03", "U04"), ("U04", "U05")):
    A, B = data[a], data[b]
    for tag in A["c"]:
        if tag not in B["c"]: continue
        ha, hb = home_x(A, tag, 1.0), home_x(B, tag, 1.0)
        if ha is None or hb is None or ha[1] != hb[1]: continue
        dn = B["c"][tag]["n60"] - A["c"][tag]["n60"]
        if dn != 0:
            print(f"  {a}->{b} {tag}: n60 {A['c'][tag]['n60']}->{B['c'][tag]['n60']} dX={hb[0]-ha[0]:+.3f}")

print()
print("variants of the strict subset (min total 3): with / without n60 in the sameness test")
for a, b in (("U03", "U04"), ("U04", "U05")):
    A, B = data[a], data[b]
    for use_n60 in (True, False):
        su, nz = 0, []
        for tag in A["c"]:
            if tag not in B["c"]: continue
            ha, hb = home_x(A, tag, 3.0), home_x(B, tag, 3.0)
            if ha is None or hb is None: continue
            ca, cb = A["c"][tag], B["c"][tag]
            same = (ha[1] == hb[1] and ca["tech"][1] == cb["tech"][1] and ca["ideas"] == cb["ideas"] and ca["reforms"] == cb["reforms"] and ca["modkeys"] == cb["modkeys"] and (ca["n60"] == cb["n60"] or not use_n60))
            if same:
                su += 1
                if abs(hb[0] - ha[0]) > 0.0015: nz.append((tag, round(hb[0] - ha[0], 3)))
        print(f"  {a}->{b} n60 in test={use_n60}: strict {su}, nonzero {len(nz)}")
print("YEM home X by save:", {sid: (round(home_x(data[sid], 'YEM', 1.0)[0], 3), home_x(data[sid], 'YEM', 1.0)[1], data[sid]['c']['YEM']['n60']) for sid in PLAYED if home_x(data[sid], 'YEM', 1.0)})
print("MKL merchant residual nodes U04:", sorted(n for n, nn in data['U04']['nodes'].items() if 'MKL' in nn['e'] and nn['e']['MKL']['trader']), " U05:", sorted(n for n, nn in data['U05']['nodes'].items() if 'MKL' in nn['e'] and nn['e']['MKL']['trader']))
# pairs at entry level (one pair per away-collecting merchant entry)
print("pairs at entry level (away entry X - home X, min total 3):")
for sid in PLAYED:
    s = data[sid]; cnt = Counter()
    for tag in s["c"]:
        hx = home_x(s, tag)
        if hx is None: continue
        for ax in away_xs(s, tag):
            cnt[("home merchant" if hx[1] else "home no merchant", round(ax - hx[0], 2) + 0.0)] += 1
    print(f"  {sid}: {dict(sorted(cnt.items()))}")
