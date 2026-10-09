"""R08 Q2: what is the country-level steering strength a_c = add*rank? Compare with X, merchants, prestige, etc. in one save."""
import sys, statistics, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V
import venice_b_9_weights_a as A
import venice_b_14_xsteps as XS
tag = sys.argv[1] if len(sys.argv) > 1 else '1445_07_02'
p = [x for x in V.files() if x.stem.endswith(tag)][0]
ns = V.nodes(p); cs = V.load(p, 'countries')
a = A.country_a(ns); X = XS.xs(p)
rows = [(c, round(a[c], 4), round(X[c], 3) if c in X else None) for c in a if c in cs]
# group by a to see how many distinct levels
lv = collections.Counter(round(v, 2) for _, v, _ in rows)
print(sorted(lv.items())[:40])
pairs = [(v, x) for _, v, x in rows if x]
import numpy as np
print('corr a vs X', np.corrcoef([p[0] for p in pairs], [p[1] for p in pairs])[0, 1], len(pairs))
for c, v, x in sorted(rows, key=lambda r: -r[1])[:12]: print(c, v, x, cs[c].get('government_rank'), cs[c].get('num_of_trade_embargos'), cs[c].get('technology', {}).get('dip_tech') if isinstance(cs[c].get('technology'), dict) else '')
