import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, collections, math, pickle
from app.trade import game_data
g = game_data.graph()
rows, nodes = fl.load()
data = [r for r in rows if set(r) - {'max_demand','sid','node','tag','date'}]
print('entries with data keys', len(data), ' with max_pow', sum(1 for r in data if 'max_pow' in r), 'with prev', sum(1 for r in data if 'prev' in r))
pp = {(r['sid'], r['node'], r['tag']): r.get('province_power', 0.0) for r in data}
def tr(x): return math.trunc(x*1000+1e-9)/1000
def rd(x): return math.floor(x*1000+0.5+1e-9)/1000
variants = {
 'sum/5 exact (tol .0011)': lambda ps: sum(ps)/5,
 'trunc3(sum/5)': lambda ps: tr(sum(ps)/5),
 'sum(trunc3(p/5))': lambda ps: sum(tr(p/5) for p in ps),
 'round3(sum/5)': lambda ps: rd(sum(ps)/5),
 'sum(round3(p/5))': lambda ps: sum(rd(p/5) for p in ps),
}
res = {}
for name, fn in variants.items():
    ok = 0; fails = []
    for r in data:
        ps = [pp.get((r['sid'], d, r['tag']), 0.0) for d in g.outgoing(r['node'])]
        ps = [p for p in ps if p >= 10]
        p = fn(ps); rec = r.get('prev', 0.0)
        if abs(p-rec) < 0.00051: ok += 1
        else: fails.append((r['sid'], r['node'], r['tag'], rec, p))
    res[name] = fails
    print(name, 'ok', ok, 'fail', len(fails), 'of', len(data))
pickle.dump(res, open('/tmp/eu4research/cache/r05_variants.pkl','wb'))
