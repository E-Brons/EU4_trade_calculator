"""Verifier (independent): distribution of the foreign-node max_demand per non-embargoed (save, country)."""
import sys, pickle, collections, statistics
sys.path.insert(0, 'scripts/research')
import common
vals = {}; extra = collections.Counter()
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    for tag, c in m['countries'].items():
        if c.get('trade_embargoed_by'): continue
        home = c.get('home_node'); fors = []
        for n in m['nodes']:
            t = n.get(tag)
            if not isinstance(t, dict) or 'max_demand' not in t: continue
            top = n.get('top_provinces') or []
            if n['definitions'] == home or (top and top[0] == tag): continue
            if 'total' in t and not t.get('has_capital'): continue
            fors.append(t['max_demand'])
        if fors:
            v = collections.Counter(fors).most_common(1)[0][0]
            vals[(e['id'], tag)] = v
            if home is None: extra[tag] += 1
print('groups', len(vals), 'no home_node:', dict(extra))
cnt = collections.Counter(vals.values())
print('top values', cnt.most_common(10), 'distinct', len(cnt))
print('min', min(vals.items(), key=lambda x: x[1]), 'max', max(vals.items(), key=lambda x: x[1]))
print('below 1.0:', sum(v < 1 for v in vals.values()), 'tags', len({k[1] for k, v in vals.items() if v < 1}), 'exactly 1.0:', sum(v == 1.0 for v in vals.values()), [k for k, v in vals.items() if v == 1.0][:3])
print([k for k, v in vals.items() if v == 1.0 and k[1] != 'PIR'])
import math
def corr(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    sx = math.sqrt(sum((x-mx)**2 for x in xs)); sy = math.sqrt(sum((y-my)**2 for y in ys))
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys))/(sx*sy) if sx and sy else float('nan')
res = {k: ([], []) for k in ('prestige', 'current_power_projection', 'mercantilism', 'government_rank')}
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    for tag, c in m['countries'].items():
        if (e['id'], tag) not in vals or tag == 'PIR': continue
        for k in res:
            try: x = float(c[k])
            except Exception: continue
            res[k][0].append(x); res[k][1].append(vals[(e['id'], tag)])
for k, (xs, ys) in res.items(): print(k, len(xs), round(corr(xs, ys), 3))
