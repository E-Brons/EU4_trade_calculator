"""Leaderless entries: is f constant per (save, country)?  And which country-block features separate f!=1 countries?"""
import sys, pickle
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from collections import Counter, defaultdict
A = common.as_list
rows = pickle.load(open('/tmp/eu4research/cache/u345_f_rows.pkl', 'rb'))
E = {e['id']: e for e in L.OLD + L.NEW}
bycountry = defaultdict(list)
for x in rows:
    if any(f['leader'] for f in x['fleets']): continue
    bycountry[(x['sid'], x['tag'])].append((x['node'], x['f'], x['n']))
multi = {k: v for k, v in bycountry.items() if len(v) > 1}
nonconst = {k: v for k, v in multi.items() if len({f for _, f, _ in v}) > 1}
print('leaderless (save,country) with >=2 entries:', len(multi), '; with non-constant f:', len(nonconst))
for k, v in nonconst.items(): print('  NONCONST', k, v)
odd = {k: v for k, v in bycountry.items() if any(f != 1.0 for _, f, _ in v)}
print('leaderless (save,country) with any f!=1:', len(odd))
for k, v in odd.items(): print('  ', k, v)
pickle.dump(bycountry, open('/tmp/eu4research/cache/u345_bycountry.pkl', 'wb'))
