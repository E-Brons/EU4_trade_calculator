"""Country-block features that separate the leaderless f!=1 countries (S79) from the leaderless f==1 ship-owning countries."""
import sys, pickle
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from collections import Counter, defaultdict
A = common.as_list
E = {e['id']: e for e in L.OLD + L.NEW}
bycountry = pickle.load(open('/tmp/eu4research/cache/u345_bycountry.pkl', 'rb'))

def feats(c, prefix='', depth=0, out=None):
    out = set() if out is None else out
    for k, v in c.items():
        if k in ('history', 'navy', 'army', 'ledger', 'historic_stats_cache', 'inflation_history', 'flags', 'active_relations', 'cb', 'friend_tags'):
            continue
        key = prefix + k
        if isinstance(v, dict):
            out.add(key + '{}')
            if depth < 3: feats(v, key + '.', depth + 1, out)
        elif isinstance(v, list):
            out.add(key + '[]')
            for i in v:
                if isinstance(i, dict):
                    if 'key' in i: out.add(key + '[key=' + str(i['key']) + ']')
                    elif 'name' in i and depth < 2: out.add(key + '[name=' + str(i['name']) + ']')
                else: out.add(key + '=' + str(i))
        else:
            if isinstance(v, str) or (isinstance(v, (int, float)) and abs(v) < 1000 and float(v).is_integer()): out.add(key + '=' + str(v))
            else: out.add(key)
    return out

sid = 'S79'
cs = common.block(E[sid], 'countries')
odd = [t for (s, t), v in bycountry.items() if s == sid and any(f != 1.0 for _, f, _ in v)]
ref = [t for (s, t), v in bycountry.items() if s == sid and all(f == 1.0 for _, f, _ in v)]
print(sid, 'f!=1 leaderless:', odd, ' f==1 leaderless ship countries:', len(ref))
fo = {t: feats(cs[t]) for t in odd}
fr = {t: feats(cs[t]) for t in ref}
common_odd = set.intersection(*fo.values())
print('features shared by all', len(odd), 'odd countries:', len(common_odd))
scored = []
for ft in common_odd:
    n_ref = sum(1 for t in ref if ft in fr[t])
    scored.append((n_ref, ft))
scored.sort()
print('features of ALL odd countries, by number of f==1 countries also having them (lowest first):')
for n, ft in scored[:25]: print('  ', n, '/', len(ref), ft)
# only among 1.1 group
odd11 = [t for t in odd if any(f == 1.1 for _, f, _ in bycountry[(sid, t)])]
