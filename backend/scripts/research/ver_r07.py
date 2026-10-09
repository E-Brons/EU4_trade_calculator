import sys, math, statistics; sys.path.insert(0, 'scripts/research')
from collections import Counter, defaultdict
from ver_common import *
def xint(m, t): return (m / (t + 0.001) - 1, (m + 0.001) / t - 1)
def rnd3(x): return math.floor(x * 1000 + 0.5) / 1000
def rows(ids):
    for sid in ids:
        for nid, raw, ents in nodes_of(sid):
            for t, e in ents.items():
                if 'money' in e and 'total' in e and fl(e['total'], 0) > 0:
                    yield sid, nid, raw, t, e
ALL = list(ENT); UNI = [i for i in ENT if i not in DUP]
# 1 truncation
for label, ids in (('82', ALL), ('unique80', UNI)):
    c = Counter()
    for sid, nid, raw, t, e in rows(ids):
        tot, m = fl(e['total']), fl(e['money'])
        if tot < 20: continue
        lo, hi = xint(m, tot); X = (lo + hi) / 2; g = round(X, 2)
        if abs(X - g) > 0.0006: c['off_grid'] += 1; continue
        c['n'] += 1
        tr, ro = tr3(tot * (1 + g)), rnd3(tot * (1 + g))
        c['trunc_ok'] += abs(tr - m) < 5e-4
        if abs(tr - ro) > 5e-4:
            c['differ'] += 1; c['differ_trunc_ok'] += abs(tr - m) < 5e-4; c['differ_round_ok'] += abs(ro - m) < 5e-4
    print('1 truncation', label, dict(c))
# 2 pairs
for label, ids in (('82', ALL), ('unique', list(PLAYED))):
    out = Counter(); allrules = Counter()
    for sid in ids:
        by = defaultdict(list)
        for s_, nid, raw, t, e in rows([sid]): by[t].append((nid, raw, e))
        for t, L in by.items():
            home = [x for x in L if x[2].get('has_capital')]
            if len(home) != 1: continue
            hn, hr, h = home[0]
            # rules test over all away entries
            for an, ar, a in L:
                if a is h: continue
                allrules['away_entries'] += 1
                allrules['tcr' if ar.get('trade_company_region') else 'not_tcr'] += 1
                allrules['pirate_power'] += fl(ar.get('collector_power_including_pirates'), 0) > fl(ar.get('collector_power'), 0) + 1e-9
            if fl(h['total']) < 3: continue
            hlo, hhi = xint(fl(h['money']), fl(h['total']))
            for an, ar, a in L:
                if a is h or not a.get('has_trader') or fl(a['total']) < 3: continue
                alo, ahi = xint(fl(a['money']), fl(a['total']))
                dlo, dhi = alo - hhi, ahi - hlo
                cls = ('+0.10' if dlo <= 0.10 <= dhi else '') + ('0.00' if dlo <= 0 <= dhi else '')
                out[('home_merchant' if h.get('has_trader') else 'home_no_merchant', cls or 'other')] += 1
    print('2 pairs', label, dict(out), dict(allrules))
