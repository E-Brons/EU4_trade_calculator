"""R07: step of X = money/total at the home node from the pre-tick save U09 (1444.11.30) to the first tick U10 (1444.12.01), by home-merchant state (before, after)."""
import sys, collections
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

a, b = home('1444_11_30'), home('1444_12_01')
tab = collections.defaultdict(collections.Counter)
for c in set(a) & set(b):
    tab[(a[c][0], b[c][0])][round((b[c][1] - a[c][1]) * 20) / 20] += 1
print('common countries', len(set(a) & set(b)))
for k, v in sorted(tab.items()): print('home merchant before/after', k, sum(v.values()), dict(sorted(v.items())))
