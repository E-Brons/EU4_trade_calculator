"""R01 Q4: does the country-wide foreign max_demand (cap) track saved country scalars (prestige, power projection, mercantilism, rank)?"""
import sys, os, re, collections, pickle, statistics
sys.path.insert(0, os.path.dirname(__file__))
import common
rows = pickle.loads((common.CACHE / 'r01_rows2.pkl').read_bytes())
fo = collections.defaultdict(set)
for r in rows:
    if r['emb'] or r['ishome'] or r['top'] or (r['coll'] and not r['cap']): continue
    fo[(r['save'], r['tag'])].add(r['md'])
masters = {}
def M(s):
    if s not in masters: masters[s] = pickle.loads((common.CACHE / f'master_{s}.pkl').read_bytes())['countries']
    return masters[s]
data = []
for (s, t), v in fo.items():
    if len(v) != 1: continue
    c = M(s).get(t, {})
    try:
        data.append((s, t, next(iter(v)), float(c.get('prestige', 'nan')), float(c.get('current_power_projection', 'nan')), float(c.get('mercantilism', 'nan')), float(c.get('government_rank', 'nan'))))
    except Exception: pass
import math
data = [d for d in data if not any(math.isnan(x) for x in d[3:])]
print(len(data), 'country-saves with single foreign cap and numeric fields')
print('cap < 1.0:', sum(d[2] < 1 for d in data), ' cap==1.0:', sum(abs(d[2]-1) < 0.0006 for d in data), ' cap>1:', sum(d[2] > 1.0006 for d in data))
y = [d[2] for d in data]
for j, nm in zip((3, 4, 5, 6), ['prestige', 'power_projection', 'mercantilism', 'government_rank']):
    xs = [d[j] for d in data]
    print(' corr(cap, %s) = %.3f' % (nm, statistics.correlation(xs, y)), ' slope', round(statistics.linear_regression(xs, y).slope, 5), ' R2', round(statistics.correlation(xs, y)**2, 3))
