"""R09 Q8 / R01: on tick-day saves, change of a country's max_demand at its home node (minus the median change at its other nodes) vs the change of its transfer_home_bonus."""
import sys, collections, statistics
sys.path.insert(0, 'scripts/research')
import venice_load as V
by = {p.stem[6:]: p for p in V.files()}
TICKS = ['1444_12_01', '1445_01_01', '1445_02_01', '1445_03_01', '1445_04_01', '1445_05_01', '1445_06_01', '1445_07_02']

def snap(tag):
    p = by[tag]; cs = V.load(p, 'countries'); md = collections.defaultdict(dict); home = {}
    for n in V.nodes(p):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and 'max_demand' in e:
                md[c][n['definitions']] = e['max_demand']
                if e.get('has_capital'): home[c] = n['definitions']
    return cs, md, home

prev = snap(TICKS[0]); res = collections.Counter(); rows = []
for t in TICKS[1:]:
    cur = snap(t)
    for c in cur[2]:
        if c not in prev[2] or cur[2][c] != prev[2][c]: continue
        h = cur[2][c]
        others = [n for n in cur[1][c] if n != h and n in prev[1][c]]
        if len(others) < 2: continue
        dh = cur[1][c][h] - prev[1][c][h]
        do = statistics.median(cur[1][c][n] - prev[1][c][n] for n in others)
        dthb = cur[0][c].get('transfer_home_bonus', 0) - prev[0][c].get('transfer_home_bonus', 0)
        if abs(dthb) < 1e-9: res[('thb unchanged', abs(dh - do) < 0.0105)] += 1
        else:
            ok = abs((dh - do) - dthb) < 0.0105
            res[('thb changed', ok)] += 1
            rows.append((t, c, round(dthb, 2), round(dh - do, 3), ok))
    prev = cur
print(dict(res))
for r in rows[:14]: print(r)
