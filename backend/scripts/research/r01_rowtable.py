"""R01 Q1-Q3: per-row table for one country in one save: class (home/top_provinces/other), away, md, class cap, embargoers' power."""
import sys, os, re, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
sid, tag = sys.argv[1], sys.argv[2]
m = pickle.loads((common.CACHE / f"master_{sid}.pkl").read_bytes())
c = m['countries'][tag]; emb = c.get('trade_embargoed_by') or []; home = c.get('home_node')
print(sid, tag, 'home', home, 'embargoed by', emb)
recs = []
for n in m['nodes']:
    v = n.get(tag)
    if not (isinstance(v, dict) and 'val' in v): continue
    ents = {k: x for k, x in n.items() if TAG.match(k) and isinstance(x, dict)}
    top = (n.get('top_provinces') or [None])[0]
    away = 'total' in v and not v.get('has_capital')
    pw = {q: ents[q].get('ship_power', 0) + ents[q].get('province_power', 0) for q in emb if q in ents}
    recs.append(dict(node=n['definitions'], prov=v.get('province_power', 0), top=top, ishome=n['definitions'] == home, dom=(n['definitions'] == home) or top == tag,
                     away=away, steer='type' in v, md=v['max_demand'], pw={q: x for q, x in pw.items() if x > 0}, ents=ents))
caps = {}
for cls in (True, False):
    cl = [r['md'] * (2 if r['away'] else 1) for r in recs if r['dom'] == cls and not r['pw']]
    if cl: caps[cls] = max(cl); print('clean', 'domestic' if cls else 'foreign', 'values', sorted(set(round(x, 3) for x in cl)), 'n', len(cl))
print('node | prov | top_prov[0] | class | role | md | cap(class) | red% | embargoers with prov+ship power')
for r in recs:
    cap = caps.get(r['dom']); adj = r['md'] * (2 if r['away'] else 1)
    red = (1 - adj / cap) * 100 if cap else float('nan')
    role = 'home' if r['ishome'] else ('collect-away' if r['away'] else ('steer' if r['steer'] else 'passive'))
    print(f"{r['node']:16s} {r['prov']:8.3f} {str(r['top']):4s} {'dom' if r['dom'] else 'for'} {role:12s} {r['md']:.3f} {cap if cap else float('nan'):.3f} {red:6.2f}  {r['pw']}")
