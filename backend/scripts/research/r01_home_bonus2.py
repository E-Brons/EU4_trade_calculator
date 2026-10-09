"""R01 Q3: the 16 non-embargoed countries whose md at home differs from md at a top-province node: diff vs 0.1 * steering merchants."""
import sys, os, collections, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
rows = pickle.loads((common.CACHE / 'r01_rows2.pkl').read_bytes())
by = collections.defaultdict(list)
for r in rows: by[(r['save'], r['tag'])].append(r)
out = []
allsteer = collections.Counter()
for k, rs in by.items():
    if any(r['emb'] for r in rs): continue
    steer = [r for r in rs if r['steer'] and r['v'].get('has_trader')]
    away = any(r['coll'] and not r['cap'] for r in rs)
    home = [r for r in rs if r['ishome']]; top = [r for r in rs if r['top'] and not r['ishome'] and not (r['coll'] and not r['cap'])]
    if not home or not top: continue
    d = home[0]['md'] - top[0]['md']
    homesteer = any(r['ishome'] and r['steer'] for r in rs)
    out.append((k, round(d, 3), len(steer), away, home[0]['has_power'], homesteer))
diff = [o for o in out if abs(o[1]) > 0.0015]
print('countries with both a home entry and a top-province node:', len(out), ' differing:', len(diff))
for o in diff: print(o, ' 0.1*steer =', round(0.1*o[2], 3), ' match' if abs(o[1]-0.1*o[2]) < 0.0025 else ' NO match')
# distribution of #steering merchants among equal ones
eq = [o for o in out if abs(o[1]) <= 0.0015]
print('equal ones: steering-merchant count distribution', sorted(collections.Counter(min(o[2], 10) for o in eq).items()))
print('--- split by save')
c = collections.Counter()
for o in out:
    sid = o[0][0]; grp = 'ticked/played (S79,S80,U01,U02)' if sid in ('S79', 'S80', 'U01', 'U02') else 'other saves'
    c[(grp, 'steer>=1' if o[2] >= 1 else 'steer=0', 'away' if o[3] else 'no away', 'diff' if abs(o[1]) > 0.0015 else 'equal')] += 1
for k, v in sorted(c.items()): print(v, k)
# in ticked saves, which tags are equal with steer>=1 and no away
print([o[0] for o in out if o[0][0] in ('S79',) and o[2] >= 1 and not o[3] and abs(o[1]) <= 0.0015][:15])
