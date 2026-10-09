"""TUR protect-mission table per save; non-light types inside counted fleets; largest per-node ship counts."""
import sys
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from u345_ships_reconcile import analyse, BASE, A
from collections import Counter
E = {e['id']: e for e in L.OLD + L.NEW}
for sid in ('S79', 'S80', 'U03', 'U04', 'U05'):
    r = analyse(E[sid])
    tur = [(k[1], en, fits[0][3] if len(fits) == 1 else None, [dict(f['types']) for f in fl]) for k, en, fl, fits in r['rows'] if k[0] == 'TUR']
    print('==', sid, E[sid]['date'], 'TUR entries', len(tur), 'ships', sum(t[1][0] for t in tur if t[1]), 'f values', Counter(round(t[2], 3) for t in tur if t[2]))
    if sid in ('U03', 'U04', 'U05'):
        for t in sorted(tur): print('    ', t[0], t[1], 'f', None if t[2] is None else round(t[2], 3), t[3])
    nl = Counter(); fits_with_nonlight = 0; tot_fleets = 0
    for k, en, fl, fits in r['rows']:
        if en and len(fits) == 1:
            for i in fits[0][0]:
                tot_fleets += 1
                if any(t not in BASE for t in fl[i]['types']): fits_with_nonlight += 1; nl.update({t: n for t, n in fl[i]['types'].items() if t not in BASE})
    big = sorted(((en[0], k) for k, en, fl, fits in r['rows'] if en), reverse=True)[:3]
    print('    counted fleets', tot_fleets, '; counted fleets that also contain non-light ships', fits_with_nonlight, dict(nl), '; largest entries', big)
