"""R02 Q1/Q3: every away-collecting entry (key `total`, no `has_capital`) of S79 (the goal's table save): same-class baseline, ratio, embargo explanation.
cap_class = md of the same country at same-class nodes where no embargoer has own power (own = max_pow - prev); pred = 0.5 * sum_e own_e / (sum own + 5*NH)."""
import sys, os, re, collections, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
def own(x): return x.get('max_pow', 0) - x.get('prev', 0)
sid = sys.argv[1] if len(sys.argv) > 1 else 'S79'
m = pickle.loads((common.CACHE / f"master_{sid}.pkl").read_bytes())
C = m['countries']
rows = []; stat = collections.Counter()
for tag in sorted({k for n in m['nodes'] for k, v in n.items() if TAG.match(k) and isinstance(v, dict) and 'total' in v and not v.get('has_capital')}):
    c = C.get(tag, {}); emb = c.get('trade_embargoed_by') or []; home = c.get('home_node')
    recs = []
    for n in m['nodes']:
        v = n.get(tag)
        if not (isinstance(v, dict) and 'max_demand' in v): continue
        ents = {k: x for k, x in n.items() if TAG.match(k) and isinstance(x, dict)}
        away = 'total' in v and not v.get('has_capital')
        dom = n['definitions'] == home or (n.get('top_provinces') or [None])[0] == tag
        Sown = sum(own(x) for x in ents.values()); nh = sum(1 for x in ents.values() if x.get('has_capital'))
        Pe = {q: own(ents[q]) for q in emb if q in ents and own(ents[q]) > 0.0005}
        recs.append(dict(node=n['definitions'], v=v, away=away, dom=dom, md=v['max_demand'], Pe=Pe, X=(sum(Pe.values()) / (Sown + 5 * nh) if Pe else 0.0), has_cap_node=bool(v.get('has_capital'))))
    caps = {}
    for cls in (True, False):
        cl = [r['md'] for r in recs if r['dom'] == cls and not r['away'] and not r['Pe']]
        if cl:
            cnt = collections.Counter(round(x, 3) for x in cl); caps[cls] = cnt.most_common(1)[0][0]
    for r in recs:
        if not r['away']: continue
        cap = caps.get(r['dom'])
        if cap is None:
            rows.append((tag, r['node'], 'dom' if r['dom'] else 'for', r['md'], None, None, emb, r['Pe'], 'no clean same-class baseline')); continue
        ratio = r['md'] / cap; red = 1 - ratio / 0.5
        pred = 0.5 * r['X'] / 0.5   # predicted reduction fraction = 0.5*X ... (see below)
        predred = 0.5 * r['X']
        if not r['Pe']: verdict = 'exact 0.5' if abs(r['md'] - 0.5 * cap) <= 0.0011 else 'unexplained: ratio %.3f with no embargoer' % ratio
        else: verdict = 'embargo-consistent (|diff|<=1pp)' if abs(red - predred) <= 0.01 else 'embargo present, magnitude off by %+.1fpp' % (100 * (red - predred))
        rows.append((tag, r['node'], 'dom' if r['dom'] else 'for', r['md'], cap, ratio, emb, r['Pe'], verdict))
for r in rows:
    tag, node, cl, md, cap, ratio, emb, Pe, verdict = r
    stat[verdict.split(':')[0].split(' (')[0].split(',')[0]] += 1
    print(f"{tag:4s} {node:16s} {cl} md={md:.3f} cap={cap if cap else float('nan'):.3f} md/cap={ratio if ratio else float('nan'):.3f} embargoed_by={len(emb)} embargoers_own={ {q: round(x,1) for q, x in Pe.items()} } -> {verdict}")
print(dict(stat))
