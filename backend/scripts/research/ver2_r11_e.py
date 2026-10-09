"""Second pass U-4: counted vs uncounted protect fleets and on_my_way (independent)."""
import sys
sys.path.insert(0, 'scripts/research')
import common, ver2_r11_a as V
from collections import Counter, defaultdict
SAVES = ['S79', 'S80', 'U03', 'U04', 'U05']
es = {e['id']: e for e in common.entries()}
tot = Counter(); rows = []
for sid in SAVES:
    order, ent = V.entries_with_ships(es[sid])
    cs, fl, allf = V.fleets_of(es[sid], order)
    for key, fleets in fl.items():
        fleets = [x for x in fleets if x['light']]
        if not fleets: continue
        en = ent.get(key)
        fits = V.fit(en[:2], [x for x in fl[key]]) if en else []
        # indices refer to fl[key] (all protect fleets incl. non-light): recompute on the same list
        for i, fleet in enumerate(fl[key]):
            if not fleet['light']: continue
            if not en: status = 'uncounted'
            else:
                inn = [i in x[0] for x in fits]
                status = 'counted' if inn and all(inn) else ('uncounted' if not any(inn) else 'ambiguous')
            rows.append((sid, key, fleet['id'], fleet['name'], fleet['omw'], status))
print('fleets (protect mission, with light ships):', Counter(r[0] for r in rows))
for scope, names in (('all 5 saves', SAVES), ('U03-U05', ['U03', 'U04', 'U05'])):
    sub = [r for r in rows if r[0] in names]
    print(scope, 'fleets', len(sub), Counter((r[5], r[4]) for r in sub))
unc = [r for r in rows if r[5] == 'uncounted']
print('UNCOUNTED:')
for r in unc: print('  ', r[0], r[1], r[2], r[3], 'on_my_way', r[4])
amb = [r for r in rows if r[5] == 'ambiguous']
print('ambiguous fleets', len(amb), amb[:5])
print('counted with key absent:', [r for r in rows if r[5] == 'counted' and r[4] == '<absent>'])
print('BNG id 403526:')
for r in rows:
    if str(r[2]) == '403526' or (isinstance(r[2], dict) and r[2].get('id') == 403526): print('  ', r)
