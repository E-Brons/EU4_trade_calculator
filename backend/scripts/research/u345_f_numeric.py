"""Numeric/structural fields separating the f != 1 countries from f == 1 leaderless ship owners (whole S79/S80 sets and the same-node subset)."""
import sys, pickle
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from collections import defaultdict
E = {e['id']: e for e in L.OLD + L.NEW}
rows = pickle.load(open('/tmp/eu4research/cache/u345_f_rows.pkl', 'rb'))
def leader(x): return any(f['leader'] for f in x['fleets'])
for sid in ('S79', 'S80'):
    cs = common.block(E[sid], 'countries')
    per = defaultdict(set)
    for x in rows:
        if x['sid'] == sid and not leader(x): per[x['tag']].add((x['f'], x['node']))
    six = {t for t, v in per.items() if any(f != 1.0 for f, _ in v)}
    nodes6 = {n for t in six for _, n in per[t]}
    for label, base in (('all f=1 leaderless', {t for t in per if t not in six}),
                        ('f=1 at the SAME nodes', {t for t in per if t not in six and any(n in nodes6 for _, n in per[t])})):
        def num(c, k):
            v = c.get(k)
            return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None
        keys = {k for t in six | base for k in cs[t]}
        found = []
        for k in sorted(keys):
            a = [num(cs[t], k) for t in six]; b = [num(cs[t], k) for t in base]
            if None in a or None in b or not b: continue
            if min(a) > max(b) or max(a) < min(b): found.append((k, 'six>' if min(a) > max(b) else 'six<', round(min(a), 3), round(max(a), 3), round(min(b), 3), round(max(b), 3)))
        print(sid, label, 'six', len(six), 'baseline', len(base), '-> perfectly separating numeric fields:', found)
        if sid == 'S79' and label.startswith('f=1 at'): print('   baseline tags', sorted(base))
    # structural: presence of sub-block keys
    sub = defaultdict(lambda: [0, 0])
    for t in six | {t for t in per if t not in six}:
        for k, v in cs[t].items():
            if isinstance(v, (dict, list)): sub[k][0 if t in six else 1] += 1
    nb = len(per) - len(six)
    print(sid, 'sub-block keys present in ALL six and in <=', 'few baseline:', sorted((k, c[1]) for k, c in sub.items() if c[0] == len(six) and c[1] <= 2))
    print(sid, 'sub-block keys present in NONE of the six but in all baseline:', sorted(k for k, c in sub.items() if c[0] == 0 and c[1] == nb))
    for t in sorted(six):
        c = cs[t]; print('  ', sid, t, 'tech_group', c.get('technology_group'), 'capital', c.get('capital'), 'gov', c.get('government_name'), 'rank', c.get('government_rank'), 'navy_tradition', c.get('navy_tradition'), 'development', c.get('development'), 'luck', c.get('luck'), 'human', c.get('human'))
