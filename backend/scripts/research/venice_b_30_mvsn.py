"""R07 M vs N direct test: countries whose home-node merchant (has_trader at the has_capital entry) differs between two consecutive tick-day saves; dX = change of money/total."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V
by = {p.stem[6:]: p for p in V.files()}
TICKS = ['1444_12_01', '1445_01_01', '1445_02_01', '1445_03_01', '1445_04_01', '1445_05_01', '1445_06_01', '1445_07_02']

def home(tag):
    d = {}
    for n in V.nodes(by[tag]):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('has_capital') and e.get('money') and e.get('total', 0) > 0.05:
                d[c] = (bool(e.get('has_trader')), round(e['money'] / e['total'], 3), n['definitions'])
    return d

tab = collections.defaultdict(collections.Counter)
rows = []
prev = home(TICKS[0])
for t in TICKS[1:]:
    cur = home(t)
    for c in set(cur) & set(prev):
        if cur[c][2] != prev[c][2]: continue
        d = round((cur[c][1] - prev[c][1]) * 20) / 20
        tab[(prev[c][0], cur[c][0])][d] += 1
        if prev[c][0] != cur[c][0]: rows.append((t, c, prev[c][0], cur[c][0], round(cur[c][1] - prev[c][1], 3)))
    prev = cur
for k, v in sorted(tab.items()):
    n = sum(v.values()); print('home merchant tick k -> tick k+1', k, 'countries', n, 'dX histogram', dict(sorted(v.items())))
print(len(rows), 'countries with a change of home-merchant state between consecutive ticks:'); 
for r in rows: print('  ', r)
