import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, collections, math, pickle
from app.trade import game_data
g = game_data.graph()
rows, nodes = fl.load()
idx = {(r['sid'],r['node'],r['tag']): r for r in rows if set(r)-{'max_demand','sid','node','tag','date'}}
res = pickle.load(open('/tmp/eu4research/cache/r05_variants.pkl','rb'))
f = [x for x in res['sum(trunc3(p/5))'] if x[3] > 0]
for sid, B, tag, rec, p in f:
    ds = g.outgoing(B)
    parts = [(d, idx.get((sid,d,tag),{}).get('province_power'), idx.get((sid,d,tag),{}).get('ship_power'), idx.get((sid,d,tag),{}).get('light_ship')) for d in ds]
    extra = rec - p
    print(sid, B, tag, 'rec', rec, 'pred', round(p,3), 'extra', round(extra,3), parts, 'extra*5', round(extra*5,3))
