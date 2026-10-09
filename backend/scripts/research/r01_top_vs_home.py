"""R01 Q2: is a node where the country has the highest provincial power ('top') priced like its home node or like a foreign node?"""
import sys, os, collections, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
rows = pickle.loads((common.CACHE / 'r01_rows2.pkl').read_bytes())
def cls(r):
    if r['coll'] and not r['cap'] and not r['ishome']: return 'away'
    if r['ishome']: return 'home'
    if r['top']: return 'top'
    return 'foreign'
by = collections.defaultdict(lambda: collections.defaultdict(set))
for r in rows:
    if r['emb']: continue
    by[(r['save'], r['tag'])][cls(r)].add(r['md'])
c = collections.Counter(); ex = []
for k, d in by.items():
    if 'top' in d and 'home' in d and 'foreign' in d and len(d['top']) == 1:
        t, h, f = next(iter(d['top'])), next(iter(d['home'])), next(iter(d['foreign']))
        key = ('top==home' if abs(t-h) < 0.0015 else '') + (' top==foreign' if abs(t-f) < 0.0015 else '')
        if abs(h-f) < 0.0015: key += ' [home==foreign]'
        c[key.strip() or 'top differs from both'] += 1
        if not key and len(ex) < 6: ex.append((k, t, h, f))
for k, v in c.most_common(): print(v, k)
print(ex)
# also: how many (save,country) have top nodes at all, and what do the top nodes look like in relation to home==foreign
