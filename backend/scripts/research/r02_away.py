"""R02: ratio of max_demand at away-collecting nodes to the same country's md at nodes of the same domestic/foreign class, for non-embargoed countries.
away = key `total` (collecting) and no `has_capital`. class of the away node: 'dom' if top_provinces[0]==tag (or home), else 'foreign'."""
import sys, os, collections, pickle, statistics
sys.path.insert(0, os.path.dirname(__file__))
import common
rows = pickle.loads((common.CACHE / 'r01_rows2.pkl').read_bytes())
foreign = collections.defaultdict(set); dom = collections.defaultdict(set); away = []
for r in rows:
    k = (r['save'], r['tag'])
    is_away = r['coll'] and not r['cap']
    if r['emb']: continue
    if is_away: away.append(r); continue
    if r['ishome'] or r['top']: dom[k].add(r['md'])
    else: foreign[k].add(r['md'])
res = []
for r in away:
    k = (r['save'], r['tag'])
    base = dom[k] if (r['top'] or r['ishome']) else foreign[k]
    if len(base) != 1: res.append((r, None, 'no single baseline')); continue
    b = next(iter(base)); res.append((r, r['md']/b, 'ok'))
ok = [x for x in res if x[2] == 'ok']
print('away-collecting entries (non-embargoed countries):', len(away), ' with a single same-class baseline:', len(ok), ' no baseline:', len(res)-len(ok))
bins = collections.Counter()
for r, q, _ in ok:
    bins['0.500 (0.499-0.501)' if abs(q-0.5) <= 0.0015*max(1,1/ (next(iter(foreign[(r['save'],r['tag'])]) or 1))) else ('<0.5' if q < 0.5 else '>0.5')] += 1
print(dict(bins))
qs = sorted(q for _, q, _ in ok); print('ratio quantiles min/p10/median/p90/max', [round(qs[int(p*(len(qs)-1))],4) for p in (0,.1,.5,.9,1)])
exact = [x for x in ok if abs(x[1]-0.5) <= 0.0012]
print('exact 0.5 within 3-decimal rounding of md (|md - 0.5*base| <= 0.001):', sum(abs(r['md'] - 0.5*(r['md']/q)) <= 0.0011 for r, q, _ in ok))
print('off 0.5 examples:', [(r['save'], r['tag'], r['node'], r['md'], round(q,4)) for r, q, _ in ok if abs(r['md'] - 0.5*(r['md']/q)) > 0.0011][:12])
pickle.dump([(r['save'], r['tag'], r['node'], r['md'], q, r['top'], r['ishome']) for r, q, _ in ok], open(common.CACHE / 'r02_ratios.pkl', 'wb'))
