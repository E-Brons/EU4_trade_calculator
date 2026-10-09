"""R08 Q2 controlled test: when VEN leaves/joins a steering link, every other steerer of that link must move to add*rank_old/rank_new.

Pairs: (U25 1445.03.01, U27 1445.04.01) VEN leaves alexandria L1, ragusa L1, wien L0; (U27, U28) ragusa L1 joins; (U28, U29) alexandria L1 joins;
(U29, U30) wien L0 joins.  Rank = order by `val` (descending) among the entries carrying `add` on the same link.
"""
import sys
sys.path.insert(0, 'scripts/research')
import venice_load as V
import venice_b_5_rank as R
by = {p.stem[6:]: p for p in V.files()}

def groups(tag):
    ns = V.nodes(by[tag])
    g = R.steer_groups(ns)
    out = {}
    for (node, link), lst in g.items():
        lst = sorted(lst, key=lambda ce: -ce[1].get('val', 0))
        out[(node, link)] = [(c, e['add'], e.get('val', 0)) for c, e in lst]
    return out

def compare(t0, t1, keys):
    g0, g1 = groups(t0), groups(t1)
    tot = ok = 0
    for key in keys:
        a = {c: (i + 1, add) for i, (c, add, v) in enumerate(g0.get(key, []))}
        b = {c: (i + 1, add) for i, (c, add, v) in enumerate(g1.get(key, []))}
        for c in a:
            if c == 'VEN' or c not in b: continue
            (r0, a0), (r1, a1) = a[c], b[c]
            if r0 == r1 and abs(a0 - a1) < 0.0015: tot += 1; ok += 1; continue   # unchanged rank: add unchanged (truncation tolerance)
            pred = (a0 + 0.0005) * r0 / r1
            good = abs(pred - (a1 + 0.0005)) < 0.0016 + 0.0005 * r0 / r1
            tot += 1; ok += good
            print(f'   {t0}->{t1} {key} {c}: rank {r0}->{r1}, add {a0}->{a1}, predicted {pred:.4f}  {"ok" if good else "MISS"}')
    return ok, tot

keys = [('alexandria', 1), ('ragusa', 1), ('wien', 0)]
for t0, t1, k in (('1445_03_01', '1445_04_01', keys), ('1445_04_01', '1445_05_01', keys[1:2]), ('1445_05_01', '1445_06_01', keys[:1]), ('1445_06_01', '1445_07_02', keys[2:3])):
    print(t0, '->', t1, compare(t0, t1, k))
