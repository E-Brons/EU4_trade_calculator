"""Attribute every change between two Venice saves: node fields (trade block) and VEN country block, optionally filtered."""
import sys
sys.path.insert(0, 'scripts/research')
import venice_load as V, venice_diff as D
by = {p.stem[6:]: p for p in V.files()}
a, b = sys.argv[1], sys.argv[2]
na, nb = D.nodeflat(by[a]), D.nodeflat(by[b])
keys = sorted(k for k in set(na) | set(nb) if na.get(k) != nb.get(k))
print(f'{a} -> {b}: {len(keys)} node fields')
if len(keys) < 80:
    for k in keys: print('  ', k, na.get(k), '->', nb.get(k))
ca, cb = D.flat(V.load(by[a], 'countries')['VEN']), D.flat(V.load(by[b], 'countries')['VEN'])
ck = sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k))
skip = ('active_relations', 'opinion_cache', 'their_spy', 'faction', 'ledger', '/history')
print('VEN country fields', len(ck))
for k in ck:
    if not any(s in k for s in skip): print('  ', k, ca.get(k), '->', cb.get(k))
