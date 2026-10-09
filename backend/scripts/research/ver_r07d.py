import sys; sys.path.insert(0, 'scripts/research')
from collections import Counter, defaultdict
from ver_common import *
exec(open('scripts/research/ver_r07c.py').read().split("print('home collectors")[0])
tab = defaultdict(Counter)
for t, (X, e, lo, hi) in D.items():
    c = C.get(t)
    if not isinstance(c, dict): continue
    tc = c.get('technology') or {}
    rs = (c.get('government') or {}).get('reform_stack', {}) if isinstance(c.get('government'), dict) else {}
    reforms = tuple(sorted(r for r in lst(rs.get('reforms')) if r not in ('monarchy_mechanic', 'republic_mechanic')))
    tab[(tc.get('adm_tech'), reforms, c.get('mercantilism'))][round(X, 2)] += 1
for k in ('SWE','DAN','BRA'):
    c=C[k]; print(k, round(D[k][0],3), 'merc', c.get('mercantilism'), 'reforms', (c.get('government') or {}).get('reform_stack',{}).get('reforms'), 'relig', c.get('religion'), 'gov_rank', c.get('government_rank'))
print('--- tech3 groups keyed (reform, mercantilism) -> X counts')
for (tl, rf, mc), v in sorted(tab.items(), key=lambda kv: (-sum(kv[1].values()))):
    if tl == 3 and sum(v.values()) >= 1: print(rf, mc, dict(v))
