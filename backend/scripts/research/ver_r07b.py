import sys, math, statistics; sys.path.insert(0, 'scripts/research')
from collections import Counter, defaultdict
from ver_common import *
from ver_r07 import xint, rows
# rules on unique played saves: predict away X from home X
RULES = {
 'M': lambda a, h: 0.1 if a.get('has_trader') else 0.0,
 'N': lambda a, h: 0.1 if (a.get('has_trader') and not a.get('has_capital') and not h.get('has_trader')) else 0.0,
 'A': lambda a, h: 0.1 if (a.get('has_trader') and not a.get('has_capital')) else 0.0,
 'Z': lambda a, h: 0.0}
res = defaultdict(Counter); tags = defaultdict(set)
for sid in PLAYED:
    by = defaultdict(list)
    for s_, nid, raw, t, e in rows([sid]): by[t].append((nid, e))
    for t, L in by.items():
        home = [e for n, e in L if e.get('has_capital')]
        if len(home) != 1: continue
        h = home[0]
        hlo, hhi = xint(fl(h['money']), fl(h['total']))
        for nm, r in RULES.items():
            for n, a in L:
                if a is h: continue
                alo, ahi = xint(fl(a['money']), fl(a['total']))
                b = r(h, h)
                # X0 in [hlo-b, hhi-b]; away X = X0 + r(a) must intersect [alo, ahi] (+ margin for 3-dec truncation, 0.0011/total)
                lo, hi = hlo - b + r(a, h), hhi - b + r(a, h)
                ok = lo <= ahi + 1e-9 and hi >= alo - 1e-9
                res[nm][('home_merch' if h.get('has_trader') else 'home_nomerch', ok)] += 1
for nm, c in res.items(): print('3 rule', nm, dict(c))
# tags behind the pairs
pt = defaultdict(set)
for sid in PLAYED:
    by = defaultdict(list)
    for s_, nid, raw, t, e in rows([sid]): by[t].append((nid, e))
    for t, L in by.items():
        home = [e for n, e in L if e.get('has_capital')]
        if len(home) == 1 and fl(home[0]['total']) >= 3 and any(a is not home[0] and a.get('has_trader') and fl(a['total']) >= 3 for n, a in L):
            pt[('merch' if home[0].get('has_trader') else 'nomerch', sid)].add(t)
print('3b tags in pairs', {k: sorted(v) for k, v in pt.items()})
# 4 cross-section medians
print('4 cross-section')
for sid in ('S01', 'S36', 'S37', 'S38', 'S42', 'S78', 'S79', 'S80'):
    m, n_ = [], []
    for s_, nid, raw, t, e in rows([sid]):
        if e.get('has_capital') and fl(e['total']) >= 0.4:
            lo, hi = xint(fl(e['money']), fl(e['total'])); (m if e.get('has_trader') else n_).append((lo + hi) / 2)
    print('  ', sid, 'merchant', round(statistics.median(m), 3), len(m), 'none', round(statistics.median(n_), 3), len(n_))
