"""R01 Q1: verdict per TUR row below its class cap (S79). own = max_pow - prev. pred = 0.5 * sum_e own_e / (sum own + 5*NH)."""
import sys, os, re, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
def own(x): return x.get('max_pow', 0) - x.get('prev', 0)
sid, tag = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ('S79', 'TUR')
m = pickle.loads((common.CACHE / f"master_{sid}.pkl").read_bytes())
c = m['countries'][tag]; emb = c['trade_embargoed_by']; home = c['home_node']
rec = []
for n in m['nodes']:
    v = n.get(tag)
    if not (isinstance(v, dict) and 'val' in v): continue
    ents = {k: x for k, x in n.items() if TAG.match(k) and isinstance(x, dict)}
    away = 'total' in v and not v.get('has_capital')
    dom = n['definitions'] == home or (n.get('top_provinces') or [None])[0] == tag
    Sown = sum(own(x) for x in ents.values()); nh = sum(1 for x in ents.values() if x.get('has_capital'))
    Pe = {q: own(ents[q]) for q in emb if q in ents and own(ents[q]) > 0.0005}
    rec.append(dict(node=n['definitions'], dom=dom, away=away, md=v['max_demand'], Pe=Pe, Sown=Sown, nh=nh))
caps = {k: max(r['md'] * (2 if r['away'] else 1) for r in rec if r['dom'] == k and not r['Pe']) for k in (True, False) if any(r['dom'] == k and not r['Pe'] for r in rec)}
print('caps from rows with no embargoer own power:', caps)
print('node | class | md | cap | obs red% | pred 0.5*X % | diff pp | embargoers own power | verdict')
for r in rec:
    cap = caps.get(r['dom']); adj = r['md'] * (2 if r['away'] else 1); red = 100 * (1 - adj / cap)
    X = sum(r['Pe'].values()) / (r['Sown'] + 5 * r['nh']) if r['Pe'] else 0
    pred = 50 * X; d = red - pred
    if abs(red) < 0.005 and not r['Pe']: continue
    verdict = 'reproduced (<=1pp)' if abs(d) <= 1 else ('not reproduced' )
    print(f"{r['node']:15s} {'dom' if r['dom'] else 'for'}{'/away' if r['away'] else ''} {r['md']:.3f} {cap*(0.5 if r['away'] else 1):.4f} {red:6.2f} {pred:6.2f} {d:+6.2f}  { {q: round(x,1) for q, x in r['Pe'].items()} }  {verdict}")
