"""R01 Q1: numerator = own power (max_pow - prev: province+ship+flat extras, no propagation); sweep the NH coefficient a in D = sum(own) + a*NH."""
import sys, os, re, collections, pickle, statistics
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
def own(x): return x.get('max_pow', 0) - x.get('prev', 0)
rows = []
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    for tag, c in m['countries'].items():
        emb = c.get('trade_embargoed_by')
        if not emb: continue
        home = c.get('home_node'); recs = []
        for n in m['nodes']:
            v = n.get(tag)
            if not (isinstance(v, dict) and 'max_demand' in v): continue
            ents = {k: x for k, x in n.items() if TAG.match(k) and isinstance(x, dict)}
            away = ('total' in v) and not v.get('has_capital')
            dom = (n['definitions'] == home) or ((n.get('top_provinces') or [None])[0] == tag)
            recs.append(dict(node=n['definitions'], md=v['max_demand'] * (2.0 if away else 1.0), dom=dom, ents=ents))
        caps = {}
        for cls in (True, False):
            cl = [r['md'] for r in recs if r['dom'] == cls and not any(own(r['ents'].get(q, {})) > 0 for q in emb)]
            if cl: caps[cls] = collections.Counter(round(x, 3) for x in cl).most_common(1)[0][0]
        for r in recs:
            cap = caps.get(r['dom'])
            if not cap: continue
            ents = r['ents']; pw = [q for q in emb if q in ents and own(ents[q]) > 0.0005]
            rows.append(dict(save=e['id'], tag=tag, emb=emb, node=r['node'], cap=cap, red=1 - r['md'] / cap, ents=ents, pw=pw))
print(len(rows), 'rows')
c = collections.Counter(('some embargoer has own power' if r['pw'] else 'none has own power', 'reduced' if r['red'] > 0.003 else 'not reduced') for r in rows)
for k, v in sorted(c.items()): print(k, v)
single = [r for r in rows if len(r['pw']) == 1 and r['red'] > 0.003]
print('single embargoer with own power, reduced:', len(single))
for a in (0, 1, 2, 3, 4, 5, 6, 8, 10):
    grp = collections.defaultdict(list)
    for r in single:
        ents = r['ents']; q = r['pw'][0]
        D = sum(own(x) for x in ents.values()) + a * sum(1 for x in ents.values() if x.get('has_capital'))
        grp[(r['save'], q)].append(r['red'] * D / own(ents[q]))
    sp = [max(v) - min(v) for v in grp.values() if len(v) >= 3]
    print(f'a={a:2d}: groups {len(sp)}, median spread of implied k {statistics.median(sp):.4f}, share spread<0.02: {sum(s < 0.02 for s in sp)/len(sp):.2f}, median k {statistics.median([statistics.median(v) for v in grp.values()]):.3f}')
nr = [r for r in rows if r['pw'] and r['red'] <= 0.003]
def Xof(r):
    ents = r['ents']; D = sum(own(x) for x in ents.values()) or 1
    return sum(own(ents[q]) for q in r['pw']) / D
xs = sorted(Xof(r) for r in nr)
print('embargoer has own power but md not reduced: n', len(nr), ' share X quantiles (min/median/p90/max):', [round(xs[int(p*(len(xs)-1))], 4) for p in (0, .5, .9, 1)])
xr = sorted(Xof(r) for r in rows if r['pw'] and r['red'] > 0.003)
print('reduced rows X quantiles:', [round(xr[int(p*(len(xr)-1))], 4) for p in (0, .1, .5, .9, 1)])
print('not-reduced with X>0.01:', sum(x > 0.01 for x in xs), 'of', len(xs))
print('not-reduced examples', [(r['save'], r['tag'], r['node'], r['pw'], round(Xof(r), 4)) for r in nr if Xof(r) > 0.02][:6])
