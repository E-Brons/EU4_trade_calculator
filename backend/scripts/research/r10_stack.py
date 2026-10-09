"""R10 Q6: several embargoers at one node: additive vs multiplicative stacking (same x_e = own_e/(sum own + 5NH) shares; fit one scale k per form on all rows)."""
import sys, os, re, collections, pickle, math
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
            Sown = sum(own(x) for x in ents.values()); nh = sum(1 for x in ents.values() if x.get('has_capital'))
            xs = [own(ents[q]) / (Sown + 5 * nh) for q in emb if q in ents and own(ents[q]) > 0.0005]
            recs.append(dict(md=v['max_demand'] * (2.0 if away else 1.0), dom=dom, xs=xs))
        caps = {}
        for cls in (True, False):
            cl = [r['md'] for r in recs if r['dom'] == cls and not r['xs']]
            if cl: caps[cls] = collections.Counter(round(x, 3) for x in cl).most_common(1)[0][0]
        for r in recs:
            cap = caps.get(r['dom'])
            if cap and r['xs']: rows.append((1 - r['md'] / cap, r['xs']))
multi = [r for r in rows if len(r[1]) >= 2]; single = [r for r in rows if len(r[1]) == 1]
print('rows with embargoer own power:', len(rows), ' single-embargoer:', len(single), ' >=2 embargoers:', len(multi))
def fit(rs, f):
    num = sum(red * f(xs) for red, xs in rs); den = sum(f(xs) ** 2 for _, xs in rs); k = num / den
    rmse = math.sqrt(sum((red - k * f(xs)) ** 2 for red, xs in rs) / len(rs)); return k, rmse
add = lambda xs: sum(xs); mult = lambda xs: 1 - math.prod(1 - x for x in xs)
for nm, rs in (('single', single), ('multi (>=2)', multi), ('all', rows)):
    for fn, f in (('additive sum x_e', add), ('multiplicative 1-prod(1-x_e)', mult)):
        k, r = fit(rs, f); print(f'{nm:12s} {fn:30s} k={k:.3f} rmse={r:.4f}')
# k fitted on single rows applied to multi rows
k_add, _ = fit(single, add); k_mul, _ = fit(single, mult)
for fn, f, k in (('additive', add, k_add), ('multiplicative', mult, k_mul)):
    rm = math.sqrt(sum((red - k * f(xs)) ** 2 for red, xs in multi) / len(multi)); print(f'k from single rows ({k:.3f}) applied to multi rows, {fn}: rmse {rm:.4f}')
# can the reduction exceed 0.5*sum? check max observed reduction
print('max observed reduction (md/cap):', round(max(r for r, _ in rows), 3), ' rows with reduction > 0.5:', sum(r > 0.5 for r, _ in rows))
