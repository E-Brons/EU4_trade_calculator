"""R01 Q3: most common country-wide foreign md values; values below 1."""
import sys, os, collections, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
rows = pickle.loads((common.CACHE / 'r01_rows2.pkl').read_bytes())
fo = collections.defaultdict(set)
for r in rows:
    if r['emb'] or r['ishome'] or r['top'] or (r['coll'] and not r['cap']): continue
    fo[(r['save'], r['tag'])].add(r['md'])
vals = [next(iter(v)) for v in fo.values() if len(v) == 1]
c = collections.Counter(vals)
print('n', len(vals), 'distinct values', len(c)); print('top values', c.most_common(8))
print('share of country-saves at the 8 most common values', round(sum(n for _, n in c.most_common(8))/len(vals), 3))
print('min', min(vals), 'max', max(vals))
low = sorted((v, k) for k, v in ((k, next(iter(s))) for k, s in fo.items() if len(s) == 1) if v < 1)
print('below 1.0:', len(low), 'examples', [(k[0], k[1], v) for v, k in low[:8]])
print('below-1 tags (distinct):', len({k[1] for _, k in low}), collections.Counter(k[1] for _, k in low).most_common(8))
