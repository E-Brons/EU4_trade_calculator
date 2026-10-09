"""R07: X = money/total at venice over the series; and the change of X of all collecting countries across the first tick."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V

def X_by_country(p):
    d = collections.defaultdict(list)
    for n in V.nodes(p):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('money') and e.get('total'):
                d[c].append(e['money'] / e['total'])
    return {c: sum(v) / len(v) for c, v in d.items()}, d

prev = None
for p in V.files():
    tag = p.stem[6:]
    ns = {n['definitions']: n for n in V.nodes(p)}
    e = ns['venice']['VEN']
    X, d = X_by_country(p)
    spread = max(d['VEN']) - min(d['VEN']) if d['VEN'] else None
    print(tag, 'venice money', e.get('money'), 'total', e.get('total'), 'X', round(e['money'] / e['total'], 4), 'VEN all-node X', round(X.get('VEN', 0), 4), 'nodes', len(d['VEN']), 'thb', V.load(p, 'countries')['VEN'].get('transfer_home_bonus'))
