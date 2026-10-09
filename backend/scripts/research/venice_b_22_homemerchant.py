"""R07 M vs N: natural experiment. Countries whose home-node merchant (has_trader at the has_capital entry) appears/disappears between two consecutive saves; delta X = money/total."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V

def home(p):
    d = {}
    for n in V.nodes(p):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('has_capital') and e.get('money') and e.get('total', 0) > 0.05:
                d[c] = (bool(e.get('has_trader')), e['money'] / e['total'], n['definitions'], e.get('type'))
    return d

fs = V.files(); prev = None
tot = collections.Counter(); rows = []
for p in fs:
    cur = home(p); tag = p.stem[6:]
    if prev:
        for c in set(cur) & set(prev[1]):
            (m0, x0, n0, _), (m1, x1, n1, _) = prev[1][c], cur[c]
            if n0 != n1: continue
            flip = (m0, m1)
            tot[flip] += 1
            if m0 != m1: rows.append((prev[0], tag, c, n0, m0, m1, round(x1 - x0, 3)))
    prev = (tag, cur)
print('home-merchant state transitions (merchant before, after): counts', dict(tot))
for r in rows: print(r)
# the steady-state comparison: X with and without a home merchant on the last tick-day save
last = home(fs[-1]); import statistics
print('07.02: countries with home merchant', sum(1 for v in last.values() if v[0]), 'without', sum(1 for v in last.values() if not v[0]))
