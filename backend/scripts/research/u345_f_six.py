"""The leaderless f != 1 countries: who/when/where, the 'luck' marker, and exact separator search vs the f == 1 ship owners."""
import sys, pickle
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from collections import Counter, defaultdict
E = {e['id']: e for e in L.OLD + L.NEW}
rows = pickle.load(open('/tmp/eu4research/cache/u345_f_rows.pkl', 'rb'))
by = defaultdict(list)                      # (sid, tag) -> entries
for x in rows: by[(x['sid'], x['tag'])].append(x)

def leader(ent): return any(f['leader'] for f in ent['fleets'])
# leaderless (save, tag): f vector
info = {}
for k, ents in by.items():
    if any(leader(x) for x in ents): continue
    fs = {x['f'] for x in ents}
    info[k] = (fs.pop() if len(fs) == 1 else None, ents)
print('leaderless (save,country) pairs:', len(info), ' with non-constant f:', sum(1 for v in info.values() if v[0] is None))
odd = {k: v for k, v in info.items() if v[0] != 1.0}
print('with f != 1:', len(odd))
for k, (f, ents) in sorted(odd.items(), key=lambda kv: (kv[0][1], kv[0][0])):
    print(' ', k, 'f', f, [(x['node'], x['n'], dict(Counter({t: n for fl in x['fleets'] for t, n in fl['types'].items()})), [fl['name'] for fl in x['fleets']]) for x in ents])

# luck marker and other country-block data
countries, lucky = {}, {}
for sid in sorted({k[0] for k in info}):
    cs = common.block(E[sid], 'countries'); countries[sid] = cs
    lucky[sid] = {t for t, c in cs.items() if isinstance(c, dict) and c.get('luck')}
    print(sid, 'luck=yes tags:', sorted(lucky[sid]))
tab = Counter()
for (sid, tag), (f, ents) in info.items():
    tab[(tag in lucky[sid], 'f!=1' if f != 1.0 else 'f=1')] += 1
print('crosstab (lucky?, f) over leaderless (save,country) pairs:', dict(tab))
allf = Counter()
for (sid, tag), ents in by.items():
    allf[(tag in lucky[sid], 'leader' if any(leader(x) for x in ents) else 'no-leader', 'f!=1' if any(x['f'] != 1.0 for x in ents) else 'f=1')] += 1
print('crosstab incl. leader fleets:', dict(allf))

def feats(c):
    out = set()
    for k, v in c.items():
        if isinstance(v, (dict, list)): out.add(('has', k))
        elif isinstance(v, bool) or isinstance(v, str) or (isinstance(v, (int, float)) and abs(v) < 1e3 and float(v).is_integer()): out.add((k, str(v)))
    for k in ('flags', 'modifier', 'active_idea_groups', 'ideas', 'estate'):
        v = c.get(k)
        if isinstance(v, dict): out |= {(k, kk) for kk in v}
        elif isinstance(v, list): out |= {(k, str(i.get('modifier', i) if isinstance(i, dict) else i)) for i in v}
    return out
for sid in sorted(countries):
    six = [t for (s, t), (f, _) in info.items() if s == sid and f != 1.0]
    base = [t for (s, t), (f, _) in info.items() if s == sid and f == 1.0]
    if not six: continue
    fs = [feats(countries[sid][t]) for t in six]
    fb = [feats(countries[sid][t]) for t in base]
    allsix = set.intersection(*fs)
    sep_in = sorted(x for x in allsix if not any(x in b for b in fb))
    anybase = set.union(*fb)
    sep_out = sorted(x for x in anybase if not any(x in s_ for s_ in fs) and all(x in b for b in fb))
    print(sid, 'six:', six, 'baseline countries:', len(base), '| features in all six, in none of baseline:', sep_in[:30], '| in all baseline, in none of six:', sep_out[:30])
