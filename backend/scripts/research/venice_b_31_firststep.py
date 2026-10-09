"""R07: the extra first-tick step e in {0, 0.05} after removing the home-merchant term (0.10): which country field separates e=0 from e=0.05?"""
import sys, collections, math
sys.path.insert(0, 'scripts/research')
import venice_load as V
by = {p.stem[6:]: p for p in V.files()}

def home(tag):
    d = {}
    for n in V.nodes(by[tag]):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('has_capital') and e.get('money') and e.get('total', 0) > 0.05:
                d[c] = (bool(e.get('has_trader')), e['money'] / e['total'])
    return d

a, b = home('1444_11_30'), home('1444_12_01'); cs = V.load(by['1444_12_01'], 'countries')
rows = []
for c in set(a) & set(b):
    m0, x0 = a[c]; m1, x1 = b[c]
    if m0 != m1: continue
    e = round((x1 - x0 - (0.10 if m1 else 0.0)) * 20) / 20
    if e in (0.0, 0.05): rows.append((c, e))
print('countries', len(rows), collections.Counter(e for _, e in rows))

def flat(d, pre=''):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            if k in ('history', 'ledger', 'opinion_cache', 'active_relations', 'their_spy_network'): continue
            out.update(flat(v, pre + '/' + str(k)))
    elif isinstance(d, list):
        if len(d) <= 6:
            for i, v in enumerate(d): out.update(flat(v, pre + f'[{i}]'))
    else: out[pre] = d
    return out
F = {c: flat(cs[c]) for c, _ in rows}
cls = {c: e for c, e in rows}
best = []
keys = set().union(*[set(f) for f in F.values()])
H = lambda p: -sum(x * math.log2(x) for x in p if x > 0)
base = H([sum(1 for e in cls.values() if e == 0.05) / len(cls), sum(1 for e in cls.values() if e == 0.0) / len(cls)])
for k in keys:
    g = collections.defaultdict(list)
    for c in cls: g[F[c].get(k)].append(cls[c])
    if len(g) < 2 or len(g) > 40: continue
    cond = sum(len(v) / len(cls) * H([sum(1 for e in v if e == 0.05) / len(v), sum(1 for e in v if e == 0.0) / len(v)]) for v in g.values())
    best.append((base - cond, k, len(g)))
best.sort(reverse=True)
for gain, k, n in best[:12]: print(round(gain, 3), k, 'values', n)

print('--- by religion / technology_group')
for key in ('/religion', '/technology_group'):
    g = collections.defaultdict(collections.Counter)
    for c in cls: g[F[c].get(key)][cls[c]] += 1
    for k, v in sorted(g.items(), key=lambda kv: -sum(kv[1].values())): print(key, k, dict(v))
