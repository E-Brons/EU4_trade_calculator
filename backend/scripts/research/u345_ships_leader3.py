"""All leader-commanded protect-mission fleets in S79,S80,U03-U05: leader pips, node entry f.  Test f = 1 + 0.05*maneuver."""
import re, sys
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L, u345_ships_leader2 as Q
from u345_ships_reconcile import analyse, BASE, A
from collections import Counter
E = {e['id']: e for e in L.OLD + L.NEW}
PAT = re.compile(r'leader=\{\s*name="[^"]*"\s*type=(admiral|general)((?:\s*(?:siege|maneuver|fire|shock)=\d+)*)[^{}]*?id=\{\s*id=(\d+)\s*type=49')
for sid in ('S79', 'S80', 'U03', 'U04', 'U05'):
    e = E[sid]; t = Q.text_of(e)
    pips = {}
    for m in PAT.finditer(t):
        pips[int(m.group(3))] = (m.group(1), dict((k, int(v)) for k, v in re.findall(r'(siege|maneuver|fire|shock)=(\d+)', m.group(2))))
    r = analyse(e); cs = common.block(e, 'countries'); order = [n['definitions'] for n in common.nodes(e)]
    print('==', sid, 'leader records parsed:', len(pips))
    cnt = Counter()
    for key, en, fl, fits in r['rows']:
        tag, node = key
        for fo in A(cs[tag].get('navy')):
            if not isinstance(fo, dict) or not isinstance(fo.get('leader'), dict): continue
            m = fo.get('mission'); pm = m.get('protect_mission') if isinstance(m, dict) else None
            if not isinstance(pm, dict) or order[int(pm['node']) - 1] != node: continue
            lid = int(fo['leader']['id']); kind, p = pips.get(lid, (None, None))
            f = round(fits[0][3], 3) if en and len(fits) == 1 else None
            nfleets = len(fl)
            print(f"   {tag} {node}: fleet {fo.get('name')!r} leader {lid} {kind} {p}; entry {'yes' if en else 'NO'}; f={f}; fleets at node={nfleets}; predicted 1+0.05*maneuver = {None if p is None else round(1 + 0.05 * p.get('maneuver', 0), 3)}")
            cnt[(f is not None and p is not None and abs(f - (1 + 0.05 * p.get('maneuver', 0))) < 0.0015)] += 1
    print('   match of f with 1 + 0.05*maneuver:', dict(cnt))
