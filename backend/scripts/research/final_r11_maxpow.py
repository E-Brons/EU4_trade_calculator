"""R11 final (3/5): ship_power inside max_pow (coefficient), ships-only entry pairs, and the pool-power identity.
Independent code. Series: S79, S80, U03, U04, U05, U06 (U01/U02 are copies of S80/S79)."""
import sys, itertools, math
sys.path.insert(0, "scripts/research")
import final_r11_lib as L
from collections import Counter, defaultdict

A = L.A
CAP = 5.0   # TRADE_CAPITAL_POWER (data/game/defines_trade.json), checked below by the fit itself


def modp(c):
    return sum(L.fnum(x.get("power")) for x in A(c.get("modifier")) if isinstance(x, dict))


SER = [s for s in L.saves() if L.has_ships(s)]
print("series:", [s.id for s in SER])

# ---------- (1) coefficient of ship_power in max_pow against the same country's ship-less residual R
tot = Counter(); worst = 0.0; coefs = []
nocls = []
for s in SER:
    res = defaultdict(Counter)
    for (tag, node), c in s.ent.items():
        if "max_pow" not in c or "ship_power" in c: continue
        r = L.fnum(c["max_pow"]) - L.fnum(c.get("province_power")) - L.fnum(c.get("prev")) - modp(c) - (CAP if c.get("has_capital") else 0)
        res[(tag, bool(c.get("has_trader")))][round(r, 2)] += 1
    for (tag, node), c in s.ent.items():
        if "ship_power" not in c or "light_ship" not in c: continue
        tot["entries_with_ships"] += 1
        ref = res.get((tag, bool(c.get("has_trader"))))
        if not ref:
            nocls.append((s.id, tag, node)); continue
        R = ref.most_common(1)[0][0]
        if len(ref) > 1: tot["class_with_several_residuals"] += 1
        sp = L.fnum(c["ship_power"])
        r = L.fnum(c["max_pow"]) - L.fnum(c.get("province_power")) - L.fnum(c.get("prev")) - modp(c) - (CAP if c.get("has_capital") else 0)
        tot["tested"] += 1
        if abs(r - sp - R) <= 0.0025: tot["coef1_fits"] += 1
        else: tot["coef1_fails"] += 1; print("  coef1 FAIL", s.id, tag, node, "residual", round(r, 3), "ship", sp, "R", R)
        if abs(r - R) <= 0.0025: tot["coef0_fits"] += 1
        if sp > 0: coefs.append((r - R) / sp)
print("(1) entries with ships:", tot["entries_with_ships"], " tested (ship-less reference of the same country/merchant class):", tot["tested"],
      " coefficient 1 fits:", tot["coef1_fits"], " coefficient 0 fits:", tot["coef0_fits"], " untestable (no ship-less entry of that country and merchant class in the save):", len(nocls))
print("    fitted coefficient (max_pow - rest - R)/ship_power: min %.4f max %.4f" % (min(coefs), max(coefs)))
print("    class with several residual values:", tot["class_with_several_residuals"])

# ---------- (2) val = fx(max_pow * max_demand) for ship entries
bad = 0; n = 0
for s in SER:
    for (tag, node), c in s.ent.items():
        if "light_ship" in c and "max_demand" in c:
            n += 1
            if abs(L.fnum(c["val"]) - L.fnum(c["max_pow"]) * L.fnum(c["max_demand"])) > 0.0015 + 1e-9: bad += 1
print("(2) ship entries with val == max_pow*max_demand (|diff|<=0.0015):", n - bad, "of", n)

# modal residual R of each (save, tag, merchant flag) from ship-less entries only
RMAP = {}
for s in SER:
    res = defaultdict(Counter)
    for (tag, node), c in s.ent.items():
        if "max_pow" not in c or "ship_power" in c: continue
        r = L.fnum(c["max_pow"]) - L.fnum(c.get("province_power")) - L.fnum(c.get("prev")) - modp(c) - (CAP if c.get("has_capital") else 0)
        res[(tag, bool(c.get("has_trader")))][round(r, 2)] += 1
    RMAP[s.id] = {k: v.most_common(1)[0][0] for k, v in res.items()}

# ---------- (3) ships-only entry pairs (all save pairs i<j and consecutive pairs)
def key_fields(c):
    return (L.fnum(c.get("province_power")), L.fnum(c.get("prev")), bool(c.get("has_capital")), round(modp(c), 4), bool(c.get("has_trader")),
            "type" in c, "total" in c)

pairs = []
for i, j in itertools.combinations(range(len(SER)), 2):
    a, b = SER[i], SER[j]
    for k in set(a.ent) & set(b.ent):
        ca, cb = a.ent[k], b.ent[k]
        if "max_pow" not in ca or "max_pow" not in cb: continue
        pa, pb = key_fields(ca), key_fields(cb)
        if abs(pa[0] - pb[0]) > 0.0015 or abs(pa[1] - pb[1]) > 0.0015 or pa[2:] != pb[2:]: continue
        ra_, rb_ = RMAP[a.id].get((k[0], pa[4])), RMAP[b.id].get((k[0], pb[4]))
        if ra_ is None or rb_ is None or abs(ra_ - rb_) > 0.0025: continue     # merchant constant R (read off ship-less entries) unchanged
        dsp = L.fnum(cb.get("ship_power")) - L.fnum(ca.get("ship_power"))
        if abs(dsp) < 0.4: continue
        dmp = L.fnum(cb["max_pow"]) - L.fnum(ca["max_pow"])
        ok_mp = abs(dmp - dsp) <= 0.0025
        ok_val = all(abs(L.fnum(x["val"]) - L.fnum(x["max_pow"]) * L.fnum(x["max_demand"])) <= 0.0015 + 1e-9 for x in (ca, cb))
        role = "steer" if pa[5] else ("collect" if pa[6] or pa[2] else "passive")
        same_md = abs(L.fnum(ca["max_demand"]) - L.fnum(cb["max_demand"])) <= 0.0015
        pairs.append((a.id, b.id, k, round(dsp, 3), round(dmp, 3), ok_mp, ok_val, role, same_md, i, j))
cons = [p for p in pairs if p[10] == p[9] + 1]
print("(3) ships-only entry pairs (all save pairs):", len(pairs), " d(max_pow)==d(ship_power):", sum(p[5] for p in pairs), " val==max_pow*max_demand both ends:", sum(p[6] for p in pairs),
      " roles:", dict(Counter(p[7] for p in pairs)), " max_demand unchanged:", sum(p[8] for p in pairs))
print("    consecutive-save pairs:", len(cons), sum(p[5] for p in cons), dict(Counter(p[7] for p in cons)))
print("    distinct (tag,node) entries involved:", len({p[2] for p in pairs}), " ships added:", sum(1 for p in pairs if p[3] > 0), " ships removed:", sum(1 for p in pairs if p[3] < 0))
for p in pairs:
    if not (p[5] and p[6]): print("  PAIR FAIL", p)
for p in cons: print("   cons", p[:9])

# ---------- (4) pool identity: rule B membership per save, recorded pull/retain change vs summed eff change
G = L.GRAPH
DOWN = {}
def down(n):
    if n not in DOWN:
        st = set()
        for o in G[n]["outgoing"]:
            st.add(o["target"]); st |= down(o["target"])
        DOWN[n] = st
    return DOWN[n]
for n in G: down(n)

def eff(c): return L.fnum(c.get("val")) - L.fnum(c.get("t_out")) + L.fnum(c.get("t_in"))

def pools(s):
    coll = defaultdict(set); steer = defaultdict(set)
    for (tag, node), c in s.ent.items():
        if "total" in c or c.get("has_capital"): coll[tag].add(node)
        if "type" in c: steer[tag].add(node)
    out = {}
    for n in s.node_by_id:
        if n not in G: continue
        ret = 0.0; pul = 0.0; mem_r = {}; mem_p = {}
        for (tag, node), c in s.ent.items():
            if node != n: continue
            e = eff(c); collects = "total" in c or bool(c.get("has_capital")); st = "type" in c
            if collects: ret += e; mem_r[tag] = e
            if st or (not collects and ((coll[tag] | steer[tag]) & down(n))): pul += e; mem_p[tag] = e
        out[n] = (ret, pul, mem_r, mem_p)
    return out

PO = {s.id: pools(s) for s in SER}
rows = []
for p in pairs:
    a, b, (tag, node), dsp = p[0], p[1], p[2], p[3]
    sa, sb = next(s for s in SER if s.id == a), next(s for s in SER if s.id == b)
    na, nb_ = sa.node_by_id[node], sb.node_by_id[node]
    ra, pa_, mra, mpa = PO[a][node]; rb, pb_, mrb, mpb = PO[b][node]
    for pool, rec_key, idx, mems in (("retain", "retain_power", 0, (mra, mrb)), ("pull", "pull_power", 1, (mpa, mpb))):
        if tag not in mems[0] or tag not in mems[1]: continue      # TUR counted in this pool at both ends
        if rec_key not in na or rec_key not in nb_: continue
        rec = L.fnum(nb_[rec_key]) - L.fnum(na[rec_key])
        own = mems[1][tag] - mems[0][tag]
        allsum = (rb if idx == 0 else pb_) - (ra if idx == 0 else pa_)
        others = allsum - own
        rows.append((a, b, tag, node, pool, round(rec, 3), round(own, 3), round(allsum, 3), round(others, 3)))
print("(4) pool rows (ship entry counted in the pool at both ends):", len(rows), " distinct (save pair, node, pool):", len({(r[0], r[1], r[3], r[4]) for r in rows}))
print("    recorded change == summed change of all pool members (|diff|<=0.0105):", sum(abs(r[5] - r[7]) <= 0.0105 for r in rows), "of", len(rows))
print("    recorded change == the ship-country's own change (|diff|<=0.0105):", sum(abs(r[5] - r[6]) <= 0.0105 for r in rows), "of", len(rows))
for r in rows: print("   ", r)

# ---------- (5) is there a recorded per-ship income effect? collecting ship-entry pairs whose node is otherwise unchanged
clean = []
for p in pairs:
    a, b, (tag, node) = p[0], p[1], p[2]
    sa, sb = next(s for s in SER if s.id == a), next(s for s in SER if s.id == b)
    ca, cb = sa.ent[(tag, node)], sb.ent[(tag, node)]
    if "total" not in ca or "total" not in cb: continue
    na, nb_ = sa.node_by_id[node], sb.node_by_id[node]
    ga = L.fnum(na.get("current")) / max(L.fnum(na.get("retention")), 1e-9); gb = L.fnum(nb_.get("current")) / max(L.fnum(nb_.get("retention")), 1e-9)
    ra, pa_, mra, mpa = PO[a][node]; rb, pb_, mrb, mpb = PO[b][node]
    own_r = (mrb.get(tag, 0) - mra.get(tag, 0))
    others_r = (rb - ra) - own_r; others_p = pb_ - pa_
    clean.append((a, b, tag, node, round(gb - ga, 3), round(others_r, 3), round(others_p, 3)))
print("(5) collecting ship-entry pairs:", len(clean), " with |d gross|<=0.002 and |d other retain|<=0.002 and |d pull|<=0.002:",
      sum(1 for c in clean if abs(c[4]) <= 0.002 and abs(c[5]) <= 0.002 and abs(c[6]) <= 0.002))
for c in clean: print("   ", c)
