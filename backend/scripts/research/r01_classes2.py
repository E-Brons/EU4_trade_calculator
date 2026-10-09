"""R01 Q2/Q3: classify nodes per country (home = node of trade_port; top = top_provinces[0]==tag; away = collecting, no capital)
and test max_demand constancy per class for non-embargoed countries."""
import sys, os, re, collections, pickle, statistics
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
rows = []   # dict per country-node
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    C = m['countries']
    for n in m['nodes']:
        top = (n.get('top_provinces') or [None])[0]
        nid = n['definitions']
        for k, v in n.items():
            if not (TAG.match(k) and isinstance(v, dict) and 'max_demand' in v) or k == 'PIR': continue
            c = C.get(k, {})
            home = c.get('home_node')
            rows.append(dict(save=e['id'], tag=k, node=nid, md=v['max_demand'], emb=bool(c.get('trade_embargoed_by')),
                             ishome=(nid == home), top=(top == k), coll=('total' in v), cap=('has_capital' in v),
                             has_power=('val' in v), ship=v.get('ship_power', 0), prov=v.get('province_power', 0),
                             steer=('type' in v), v=v))
pickle.dump(rows, open(common.CACHE / 'r01_rows2.pkl', 'wb'))
def cls(r):
    if r['coll'] and not r['cap'] and not r['ishome']: return 'away'
    if r['ishome']: return 'home'
    if r['top']: return 'top'
    return 'foreign'
by = collections.defaultdict(lambda: collections.defaultdict(set))
for r in rows:
    if r['emb']: continue
    by[(r['save'], r['tag'])][cls(r)].add(r['md'])
n = collections.Counter()
for key, d in by.items():
    for c, vals in d.items(): n[(c, len(vals) == 1)] += 1
print('non-embargoed (save,country) x class: constant? ', dict(n))
# home/top vs foreign
cmp = collections.Counter(); ratios = []
for key, d in by.items():
    if 'foreign' in d and len(d['foreign']) == 1:
        f = next(iter(d['foreign']))
        for c in ('home', 'top'):
            if c in d and len(d[c]) == 1:
                x = next(iter(d[c])); ratios.append((c, x / f))
                cmp[(c, 'lower' if x < f - 0.0015 else 'higher' if x > f + 0.0015 else 'equal')] += 1
print('domestic class vs foreign value (non-embargoed):', dict(cmp))
for c in ('home', 'top'):
    rr = [x for cc, x in ratios if cc == c]
    if rr: print(c, 'n', len(rr), 'ratio dom/foreign median', round(statistics.median(rr), 3), 'min', round(min(rr), 3), 'max', round(max(rr), 3))
# nonconstant within class
nc = [(k, c, sorted(v)) for k, d in by.items() for c, v in d.items() if len(v) > 1]
print('non-constant (save,country,class):', len(nc), collections.Counter(c for _, c, _ in nc))
print(nc[:6])
