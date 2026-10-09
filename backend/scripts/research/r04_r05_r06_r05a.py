import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, collections, math
from app.trade import game_data
g = game_data.graph()
rows, nodes = fl.load()
full = [r for r in rows if len(r) > 5 and 'max_pow' in r]
print('entries with max_pow', len(full))
pp = {(r['sid'], r['node'], r['tag']): r.get('province_power', 0.0) for r in full}
def pred(r, thr):
    s = 0.0
    for d in g.outgoing(r['node']):
        p = pp.get((r['sid'], d, r['tag']), 0.0)
        if p >= thr: s += p
    return s/5
def fx(x): return math.trunc(x*1000+1e-9)/1000
for thr in (0, 10):
    ok = bad = 0; okt=0
    fails = []
    for r in full:
        p = pred(r, thr); rec = r.get('prev', 0.0)
        if abs(p-rec) <= 0.0011: ok += 1
        else: bad += 1; fails.append((r['sid'], r['node'], r['tag'], rec, p))
        if abs(fx(p)-rec) < 1e-9: okt += 1
    print('thr', thr, 'ok', ok, 'bad', bad, 'trunc-exact', okt)
    if thr == 10:
        import pickle; pickle.dump(fails, open('/tmp/eu4research/cache/r05_fails.pkl','wb'))
        c = collections.Counter((f[1], f[2]) for f in fails); print(len(fails), c.most_common(30))
        print(collections.Counter(f[0] for f in fails).most_common())
