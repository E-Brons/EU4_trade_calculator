"""Leaders in protect-mission fleets vs f.  Which entries contain a fleet with a `leader`, and what is that leader?"""
import sys, pickle
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from u345_ships_reconcile import analyse, BASE, A
from collections import Counter

rows = pickle.load(open('/tmp/eu4research/cache/u345_f_rows.pkl', 'rb'))
E = {e['id']: e for e in L.OLD + L.NEW}
# 1) entries with / without a leader fleet, by f
tab = Counter()
for x in rows:
    has = any(f['leader'] for f in x['fleets'])
    tab[(has, x['f'])] += 1
print('(has leader fleet, f) counts:', dict(sorted(tab.items(), key=str)))
# 2) all leader fleets anywhere (also in unfit entries) : print leader record from country.leader list
for sid in ('S79', 'S80', 'U03', 'U04', 'U05'):
    cs = common.block(E[sid], 'countries'); order = [n['definitions'] for n in common.nodes(E[sid])]
    seen = []
    for x in rows:
        if x['sid'] != sid: continue
        for f in x['fleets']:
            if f['leader']:
                tag = x['tag']; lid = f['leader']
                ldrs = [l for l in A(cs[tag].get('leader')) if isinstance(l, dict)]
                print(sid, tag, x['node'], 'f', x['f'], 'fleet leader ref', lid)
print()
