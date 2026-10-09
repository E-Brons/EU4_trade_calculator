import sys, math; sys.path.insert(0, 'scripts/research')
from collections import Counter, defaultdict
from ver_common import *
def xint(m, t): return (m / (t + 0.001) - 1, (m + 0.001) / t - 1)
C = common.block(ENT['S01'], 'countries')
D = {}
for nid, raw, ents in nodes_of('S01'):
    for t, e in ents.items():
        if e.get('has_capital') and 'money' in e and fl(e.get('total'), 0) >= 0.4:
            lo, hi = xint(fl(e['money']), fl(e['total'])); D[t] = ((lo + hi) / 2, e, lo, hi)
print('home collectors total>=0.4:', len(D))
dist = Counter(round(x[0], 2) for x in D.values()); print(sorted(dist.items(), key=lambda kv: -kv[1]))
off = [(t, round(x[0], 4), round(x[2], 4), round(x[3], 4)) for t, x in D.items() if abs(x[0] - round(x[0], 2)) > 0.003]
print('off-grid (>0.003):', off[:10], len(off))
tech = Counter(); bytech = defaultdict(Counter); byreform = defaultdict(Counter); feud = []
for t, (X, e, lo, hi) in D.items():
    c = C.get(t)
    if not isinstance(c, dict): continue
    tc = c.get('technology') or {}
    lv = (tc.get('adm_tech'), tc.get('dip_tech'), tc.get('mil_tech'))
    tech[lv] += 1
    if len(set(lv)) == 1: bytech[lv[0]][round(X, 2)] += 1
    g = c.get('government') or {}
    rs = g.get('reform_stack', {}) if isinstance(g, dict) else {}
    reforms = tuple(sorted(r for r in lst(rs.get('reforms')) if r not in ('monarchy_mechanic', 'republic_mechanic')))
    for r in reforms: byreform[r][round(X, 2)] += 1
    byreform['_merchant='+str(bool(e.get('has_trader')))][round(X, 2)] += 1
    if 'feudalism_reform' in reforms and round(X, 2) != 0.07: feud.append((t, round(X, 2)))
print('tech triples', dict(tech)); print('by tech level', {k: dict(v) for k, v in bytech.items()})
for r in ('plutocratic_reform', 'steppe_horde', 'signoria_reform', 'free_city', 'merchants_reform', 'feudalism_reform', 'iqta', '_merchant=True', '_merchant=False'):
    print(r, dict(byreform[r]))
print('feudalism_reform non-0.07', feud)
print('ZIM', D.get('ZIM', (None,))[0], 'SWE', round(D['SWE'][0],3), 'DAN', round(D['DAN'][0],3), 'BRA', round(D['BRA'][0],3))
print('--- mercantilism by reform (tech 3 only)')
mm = defaultdict(Counter)
for t, (X, e, lo, hi) in D.items():
    c = C.get(t)
    if not isinstance(c, dict): continue
    tc = c.get('technology') or {}
    if tc.get('adm_tech') != 3: continue
    rs = (c.get('government') or {}).get('reform_stack', {}) if isinstance(c.get('government'), dict) else {}
    for r in lst(rs.get('reforms')):
        if r in ('plutocratic_reform','steppe_horde','signoria_reform','free_city','merchants_reform','feudalism_reform','iqta'):
            mm[r][c.get('mercantilism')] += 1
for r, v in mm.items(): print(r, dict(v))
