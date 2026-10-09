"""R07 M vs N, cross-section: X by home-merchant state on several tick-day saves (same save, all countries with a has_capital collecting entry)."""
import sys, collections, statistics
sys.path.insert(0, 'scripts/research')
import venice_load as V
by = {p.stem[6:]: p for p in V.files()}
for t in ('1444_11_30', '1444_12_01', '1445_02_01', '1445_07_02'):
    g = collections.defaultdict(list)
    for n in V.nodes(by[t]):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('has_capital') and e.get('money') and e.get('total', 0) > 0.05:
                g[bool(e.get('has_trader'))].append(e['money'] / e['total'])
    q = lambda v, p: sorted(v)[int(p * (len(v) - 1))]
    print(t, {k: (len(v), round(statistics.mean(v), 3), [round(q(v, p), 3) for p in (0.1, 0.5, 0.9)]) for k, v in g.items()})
