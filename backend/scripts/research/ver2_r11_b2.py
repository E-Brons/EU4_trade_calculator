import sys
sys.path.insert(0, 'scripts/research')
import common, ver2_r11_a as V, ver2_r11_b as B
from collections import Counter, defaultdict
rows = B.collect()
# pair definitions
pairs_any = defaultdict(list)
for r in rows: pairs_any[(r['save'], r['tag'])].append(r)
only_noleader = {k: v for k, v in pairs_any.items() if all(x['status'] == 'noleader' for x in v)}
mixed = {k: [x['status'] for x in v] for k, v in pairs_any.items() if any(x['status'] != 'noleader' for x in v)}
print('pairs with no leader entry at all:', len(only_noleader), ' lucky:', sum(1 for v in only_noleader.values() if v[0]['luck']),
      ' lucky & f!=1:', sum(1 for v in only_noleader.values() if v[0]['luck'] and v[0]['f'] != 1.0))
print('pairs having a leader entry:', mixed)
print('defensive_ideas in those pairs:', Counter(v[0]['f'] for v in only_noleader.values() if 'defensive_ideas' in v[0]['groups']))
# polynesia_node entries
pn = [r for r in rows if r['node'] == 'polynesia_node']
print('polynesia_node entries', len(pn), Counter(r['f'] for r in pn), sorted({r['tag'] for r in pn if r['f'] == 1.0}))
# other nodes with f != 1 among leaderless
print('leaderless f!=1 entries by node', Counter(r['node'] for r in rows if r['status'] == 'noleader' and r['f'] != 1.0))
# leader stats
es = {e['id']: e for e in common.entries()}
for r in rows:
    if r['status'] == 'noleader': continue
    e = es[r['save']]; order, ent = V.entries_with_ships(e); cs, fl, allf = V.fleets_of(e, order)
    key = (r['tag'], r['node']); fits = V.fit(ent[key][:2], fl[key])
    ls = B.leader_stats(cs[r['tag']])
    for x in fits[:1]:
        for i in x[0]:
            L = fl[key][i]['leader']
            if L:
                s = ls.get(L['id']['id'] if isinstance(L['id'], dict) else L['id'])
                s = ls.get(L['id'])
                print(r['save'], r['tag'], r['node'], 'f', r['f'], 'leader id', L['id'], {k: s[k] for k in ('type', 'fire', 'shock', 'maneuver', 'siege') if k in s} if s else None)
# alternative single-stat hypotheses: f-1 = c * stat
import itertools
pts = []
seen = set()
for r in rows:
    if r['status'] != 'leader': continue
    e = es[r['save']]; order, ent = V.entries_with_ships(e); cs, fl, allf = V.fleets_of(e, order)
    key = (r['tag'], r['node']); fits = V.fit(ent[key][:2], fl[key]); ls = B.leader_stats(cs[r['tag']])
    L = [fl[key][i]['leader'] for i in fits[0][0] if fl[key][i]['leader']][0]
    s = ls[L['id']]
    pts.append((round(r['f'] - 1, 4), {k: s.get(k, 0) for k in ('fire', 'shock', 'maneuver', 'siege')}))
for stat in ('fire', 'shock', 'maneuver', 'siege'):
    cs_ = {round(d / p[stat], 5) for d, p in pts if p[stat]}
    zero = [d for d, p in pts if not p[stat]]
    print(stat, 'ratios (f-1)/stat:', sorted(cs_), 'entries where stat = 0 but f != 1:', zero)
