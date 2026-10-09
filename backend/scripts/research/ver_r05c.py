"""R05: ungated rule failures restricted to existing entries (the '168 of 110,589' claim)."""
import sys, json, collections
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
G = json.load(open(Path(__file__).resolve().parents[2] / 'data' / 'tradenodes.json'))['nodes']
out = {n: [o['target'] for o in v['outgoing']] for n, v in G.items()}
def d5(p): return float((D(repr(float(p))) / 5).quantize(D('0.001'), rounding=ROUND_DOWN))
def ent(c): return isinstance(c, dict) and bool(set(c) - {'max_demand'})
def tags(n): return {t: c for t, c in n.items() if isinstance(c, dict) and t.upper() == t and len(t) <= 4}
n_ent = 0; fails = []
for e in common.entries():
    ns = {n['definitions']: n for n in common.nodes(e)}; T = {k: tags(n) for k, n in ns.items()}
    for B, tg in T.items():
        for tag, c in tg.items():
            if not ent(c): continue
            n_ent += 1
            pred = sum(d5(T[D_][tag]['province_power']) for D_ in out.get(B, []) if tag in T.get(D_, {}) and T[D_][tag].get('province_power', 0) >= 10)
            rec = c.get('prev', 0.0)
            if abs(pred - rec) >= 0.0005: fails.append((e['id'], B, tag, rec, round(pred, 3)))
print('entries', n_ent, 'fail', len(fails), 'prev=0:', sum(1 for f in fails if f[3] == 0), 'rec>pred:', sum(1 for f in fails if f[3] > f[4]), 'MOR S80/U01:', sum(1 for f in fails if f[2] == 'MOR'))
print(collections.Counter((f[1], f[2]) for f in fails if f[3] == 0).most_common(8))
