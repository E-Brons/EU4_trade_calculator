"""R07: away collectors in the Venice saves: X at an away node with a merchant minus X at the home node, by home-merchant state (pairs with total >= 0.3 at both)."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V
by = {p.stem[6:]: p for p in V.files()}
for tag in ('1444_12_01', '1445_03_01', '1445_07_02'):
    g = collections.defaultdict(list); away_countries = set()
    for n in V.nodes(by[tag]):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('money') and e.get('total', 0) > 0.3:
                g[c].append((n['definitions'], bool(e.get('has_capital')), bool(e.get('has_trader')), e['money'] / e['total']))
    res = collections.Counter()
    for c, lst in g.items():
        home = [x for x in lst if x[1]]; away = [x for x in lst if not x[1] and x[2]]
        if home and away:
            for a in away: res[(home[0][2], round(a[3] - home[0][3], 2))] += 1
    print(tag, dict(sorted(res.items())))
