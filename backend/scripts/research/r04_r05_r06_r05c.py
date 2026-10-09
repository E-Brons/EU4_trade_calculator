import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, collections, math
from app.trade import game_data
g = game_data.graph()
rows, nodes = fl.load()
idx = {(r['sid'],r['node'],r['tag']): r for r in rows if set(r)-{'max_demand','sid','node','tag','date'}}
nidx = {(n['sid'], n['definitions']): n for n in nodes}
tr = lambda x: math.trunc(x*1000+1e-9)/1000
# single-link cases: exactly one downstream D with province_power>0 for this tag; B entry exists or not
cases = collections.defaultdict(list)
for (sid, node, tag), r in list(idx.items()) :
    pass
seen = set()
out = []
for (sid, D, tag), rD in idx.items():
    pD = rD.get('province_power', 0.0)
    if pD <= 0: continue
    for B in [b for b in g.nodes if D in g.outgoing(b)]:
        # all of tag's D' downstream of B
        ds = [d for d in g.outgoing(B) if idx.get((sid,d,tag),{}).get('province_power',0)>0]
        if ds != [D]: continue
        rB = idx.get((sid,B,tag))
        prev = rB.get('prev', 0.0) if rB else 0.0
        out.append(dict(sid=sid,B=B,D=D,tag=tag,pD=pD,prev=prev,contrib=prev*5/pD if pD else 0,
            has_B=rB is not None, D_has_capital=bool(rD.get('has_capital')), D_trader=bool(rD.get('has_trader')),
            D_total=nidx[(sid,D)].get('total'), D_ppow=nidx[(sid,D)].get('p_pow')))
print(len(out))
# classify by whether contributes
def label(o):
    if o['prev']==0: return 'zero'
    if abs(o['prev']-tr(o['pD']/5))<0.0006: return 'full'
    return 'other'
c = collections.Counter((label(o), 'pD>=10' if o['pD']>=10 else 'pD<10') for o in out); print(c)
zero = [o for o in out if label(o)=='zero' and o['pD']>=10]
print(collections.Counter((o['B'],o['D'],o['tag']) for o in zero).most_common(30))
import pickle; pickle.dump(out, open('/tmp/eu4research/cache/r05_single.pkl','wb'))
# for pD>=10 'full' vs 'zero': how do pD distribute?
full = [o for o in out if label(o)=='full']
print('smallest pD that propagated', sorted(o['pD'] for o in full)[:5], ' largest pD<10 that propagated:', max([o['pD'] for o in full if o['pD']<10], default=None))
print('zero w/ pD>=10: distinct (sid-independent) triples', len(set((o['B'],o['D'],o['tag'],o['pD']) for o in zero)))
