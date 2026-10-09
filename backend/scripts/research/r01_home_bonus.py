"""R01 Q3: is a home-node bonus (steering merchants, none collecting away) visible inside max_demand? Compare md at home vs md at 'top' nodes (also domestic) split by bonus-active state."""
import sys, os, collections, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
rows = pickle.loads((common.CACHE / 'r01_rows2.pkl').read_bytes())
by = collections.defaultdict(list)
for r in rows: by[(r['save'], r['tag'])].append(r)
c = collections.Counter(); ex = []
for k, rs in by.items():
    if any(r['emb'] for r in rs): continue
    steer = sum(1 for r in rs if r['steer']); away = any(r['coll'] and not r['cap'] for r in rs)
    home = [r['md'] for r in rs if r['ishome'] and not r['coll'] or (r['ishome'])]
    top = [r['md'] for r in rs if r['top'] and not r['ishome'] and not (r['coll'] and not r['cap'])]
    foreign = [r['md'] for r in rs if not r['top'] and not r['ishome'] and not (r['coll'] and not r['cap'])]
    if not home or not top: continue
    state = ('no steering merchant' if steer == 0 else ('steering>=1, nobody collects away' if not away else 'steering>=1, someone collects away'))
    same = abs(home[0] - top[0]) < 0.0015
    c[(state, 'home==top' if same else 'home!=top')] += 1
    if not same and len(ex) < 4: ex.append((k, home[0], top[0], steer, away))
for k, v in sorted(c.items()): print(v, k)
print(ex)
