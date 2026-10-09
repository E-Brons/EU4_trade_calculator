"""Track fleets by id across U03 -> U04 -> U05: mission node, on_my_way, counted?"""
import sys
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from u345_ships_reconcile import analyse, BASE, A
from collections import Counter
E = {e['id']: e for e in L.NEW}
snap = {}
for sid in ('U03', 'U04', 'U05'):
    r = analyse(E[sid]); cs = common.block(E[sid], 'countries'); order = [n['definitions'] for n in common.nodes(E[sid])]
    counted = {}
    for key, en, fl, fits in r['rows']:
        for i, f in enumerate(fl):
            counted[(key, f['name'])] = bool(en and len(fits) == 1 and i in fits[0][0])
    d = {}
    for tag, c in cs.items():
        if not isinstance(c, dict): continue
        for fo in A(c.get('navy')):
            if not isinstance(fo, dict): continue
            m = fo.get('mission'); pm = m.get('protect_mission') if isinstance(m, dict) else None
            if not isinstance(pm, dict): continue
            node = order[int(pm['node']) - 1]
            d[fo['id']['id']] = dict(tag=tag, name=fo.get('name'), node=node, omw=pm.get('on_my_way', '<absent>'), counted=counted.get(((tag, node), fo.get('name'))))
    snap[sid] = d
for sid in ('U03', 'U04', 'U05'):
    print(sid, 'protect fleets', len(snap[sid]))
print('--- fleets uncounted in a save (or omw absent) and their state in the other saves')
ids = {i for s in snap.values() for i, v in s.items() if v['counted'] is False or v['omw'] == '<absent>'}
for i in sorted(ids):
    print(i, [(sid, (snap[sid][i]['tag'], snap[sid][i]['node'], 'omw=' + str(snap[sid][i]['omw']), 'counted=' + str(snap[sid][i]['counted'])) if i in snap[sid] else None) for sid in ('U03', 'U04', 'U05')])
# fleets whose node changed between saves: counted immediately on arrival?
ch = Counter()
for a, b in (('U03', 'U04'), ('U04', 'U05')):
    for i, v in snap[b].items():
        if i in snap[a] and snap[a][i]['node'] != v['node']:
            ch[(a + '->' + b, 'omw_after=' + str(v['omw']), 'counted_after=' + str(v['counted']))] += 1
        elif i not in snap[a]:
            ch[(a + '->' + b, 'new protect fleet; omw=' + str(v['omw']), 'counted=' + str(v['counted']))] += 1
print('fleets whose node changed or that are new:', dict(ch))
