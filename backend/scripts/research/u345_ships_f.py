"""What sets f = ship_power / sum(base)?  List every f != 1 entry in S79,S80,U03-U05 with fleet/ship/country features and compare with f == 1."""
import sys, json, pickle
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from u345_ships_reconcile import analyse, BASE, A
from collections import Counter

def fleet_feats(cs, tag, order, node):
    out = []
    for fl in A(cs[tag].get('navy')):
        if not isinstance(fl, dict): continue
        m = fl.get('mission'); pm = m.get('protect_mission') if isinstance(m, dict) else None
        if not isinstance(pm, dict) or order[int(pm['node']) - 1] != node: continue
        ships = [s for s in A(fl.get('ship')) if isinstance(s, dict)]
        out.append(dict(name=fl.get('name'), keys=sorted(fl), leader=fl.get('leader'), n=len(ships), types=dict(Counter(s['type'] for s in ships)),
                        strength=sum(1 for s in ships if 'strength' in s), shipkeys=sorted({k for s in ships for k in s}),
                        morale=[round(float(s.get('morale', 0)), 2) for s in ships][:3]))
    return out

if __name__ == '__main__':
    rows = []
    for e in L.OLD + L.NEW:
        r = analyse(e); order = [n['definitions'] for n in common.nodes(e)]
        cs = common.block(e, 'countries')
        for key, en, fl, fits in r['rows']:
            if en and len(fits) == 1:
                f = round(fits[0][3], 3); tag, node = key
                rows.append(dict(sid=e['id'], tag=tag, node=node, f=f, n=en[0], fleets=fleet_feats(cs, tag, order, node)))
    pickle.dump(rows, open('/tmp/eu4research/cache/u345_f_rows.pkl', 'wb'))
    print('entries', len(rows), Counter(x['f'] for x in rows))
    for x in rows:
        if x['f'] != 1.0:
            print(x['sid'], x['tag'], x['node'], 'f', x['f'], 'ships', x['n'], 'fleets', [(f['name'], f['types'], 'leader' if f['leader'] else '-', 'strength:%d' % f['strength']) for f in x['fleets']])
    # fleet-level feature prevalence: leader, strength keys
    for feat in ('leader', 'strength'):
        a = [any((f[feat] if feat == 'leader' else f['strength'] > 0) for f in x['fleets']) for x in rows if x['f'] != 1.0]
        b = [any((f[feat] if feat == 'leader' else f['strength'] > 0) for f in x['fleets']) for x in rows if x['f'] == 1.0]
        print(feat, 'in f!=1:', sum(a), '/', len(a), ' in f==1:', sum(b), '/', len(b))
    shipkeys_a = Counter(k for x in rows if x['f'] != 1.0 for f in x['fleets'] for k in f['shipkeys']); shipkeys_b = Counter(k for x in rows if x['f'] == 1.0 for f in x['fleets'] for k in f['shipkeys'])
    print('ship keys f!=1', dict(shipkeys_a)); print('ship keys f==1', dict(shipkeys_b))
    fk_a = Counter(k for x in rows if x['f'] != 1.0 for f in x['fleets'] for k in f['keys']); fk_b = Counter(k for x in rows if x['f'] == 1.0 for f in x['fleets'] for k in f['keys'])
    print('fleet keys f!=1', dict(fk_a)); print('fleet keys f==1', dict(fk_b))
