"""Counted vs uncounted protect-mission fleets (fleet inside the unique subset that reproduces the node entry vs not), by on_my_way."""
import sys
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from u345_ships_reconcile import analyse, BASE
from collections import Counter
E = {e['id']: e for e in L.OLD + L.NEW}
tot = Counter()
for sid in ('S79', 'S80', 'U03', 'U04', 'U05'):
    r = analyse(E[sid]); c = Counter(); detail = []
    for key, en, fl, fits in r['rows']:
        if en and len(fits) == 1:
            chosen = set(fits[0][0])
            for i, f in enumerate(fl):
                c[('counted' if i in chosen else 'UNCOUNTED', str(f['omw']))] += 1
                if i not in chosen: detail.append((key, f['name'], dict(f['types']), f['omw'], f['mp'], f['cyc']))
        elif not en:
            for f in fl:
                c[('UNCOUNTED(node has no entry)', str(f['omw']))] += 1; detail.append((key, f['name'], dict(f['types']), f['omw'], f['mp'], f['cyc']))
    print('==', sid, E[sid]['date'], dict(c))
    for d in detail: print('     ', d)
    tot.update(c)
print('TOTAL', dict(tot))
