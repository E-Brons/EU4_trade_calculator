"""R05: final propagation rule  prev_B(tag) = sum over links B->D with node steer weight(B,D) > 0 and province_power_D(tag) >= 10 of trunc3(province_power_D / 5)  [+ ship term for MOR in S79/S80/U01/U02]."""
import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, pickle, collections, math, common
from common import as_list
from app.trade import game_data
g = game_data.graph()
rows, nodes = fl.load()
nidx = {(n['sid'], n['definitions']): n for n in nodes}
idx = {(r['sid'],r['node'],r['tag']): r for r in rows if set(r)-{'max_demand','sid','node','tag','date'}}
tr = lambda x: math.trunc(x*1000+1e-9)/1000
bytag = collections.defaultdict(set)
for (sid,node,tag) in idx: bytag[(sid,tag)].add(node)
def pred(sid, B, tag, thr=10, use_w=True, ships=0.0):
    s = 0.0
    sp = as_list(nidx[(sid,B)].get('steer_power'))
    for i, D in enumerate(g.outgoing(B)):
        r = idx.get((sid,D,tag))
        if not r: continue
        p = r.get('province_power', 0.0)
        if p >= thr and (not use_w or (i < len(sp) and sp[i] > 0)):
            s += tr(p/5)
        if ships and p >= thr and (not use_w or (i < len(sp) and sp[i] > 0)):
            s += r.get('ship_power', 0.0) * ships / 5
    return s
# candidate (sid,B,tag): entries that exist OR where some downstream D has province_power>=10
cands = set(k for k, r in idx.items())
for (sid,D,tag), r in idx.items():
    if r.get('province_power',0) >= 10:
        for B in g.nodes:
            if D in g.outgoing(B) and (sid,B) in nidx: cands.add((sid,B,tag))
print('candidates', len(cands))
for use_w in (False, True):
    ok = bad = 0; fails = []
    for (sid,B,tag) in cands:
        r = idx.get((sid,B,tag), {})
        p = pred(sid,B,tag,use_w=use_w); rec = r.get('prev', 0.0)
        if abs(p-rec) < 0.0006: ok += 1
        else: bad += 1; fails.append((sid,B,tag,rec,p))
    print('use steer weight' if use_w else 'no weight', 'ok', ok, 'bad', bad)
    last = fails
print(collections.Counter((f[0] in ('S79','S80','U01','U02')) for f in last))
print(collections.Counter((f[1],f[2]) for f in last).most_common(20))
pickle.dump(last, open('/tmp/eu4research/cache/r05_final_fails.pkl','wb'))
# snapshot-only subset
snap = [f for f in last if f[0] not in ('S79','S80','U01','U02')]
print('fails in the 78 start snapshots', len(snap), snap[:10])

print('=== played saves: failures explained by ignoring the weight? by MOR ship term?')
pl = [f for f in last if f[0] in ('S79','S80','U01','U02')]
c = collections.Counter()
for sid,B,tag,rec,p in pl:
    p_nw = pred(sid,B,tag,use_w=False)
    p_sh = pred(sid,B,tag,use_w=True,ships=0.25) if tag=='MOR' else None
    if abs(p_nw-rec)<0.0006: c['matches no-weight rule']+=1
    elif p_sh is not None and abs(p_sh-rec)<0.0006: c['matches MOR ship term x0.25']+=1
    else: c['neither']+=1
print(c)
# MOR in all saves: is ship term needed anywhere else?
mor = [(sid,B) for (sid,B,tag) in cands if tag=='MOR']
okw = sum(1 for sid,B in mor if abs(pred(sid,B,'MOR')-idx.get((sid,B,'MOR'),{}).get('prev',0.0))<0.0006)
oks = sum(1 for sid,B in mor if abs(pred(sid,B,'MOR',ships=0.25)-idx.get((sid,B,'MOR'),{}).get('prev',0.0))<0.0006)
print('MOR candidates', len(mor), 'ok without ship term', okw, 'ok with ship term', oks)
# MOR sids
print(collections.Counter(sid for sid,B in mor if abs(pred(sid,B,'MOR')-idx.get((sid,B,'MOR'),{}).get('prev',0.0))>=0.0006))
# other countries with downstream ship power in played saves: match without ship term?
others = [(sid,B,tag) for (sid,B,tag) in cands if sid in ('S80',) and tag!='MOR' and any(idx.get((sid,D,tag),{}).get('ship_power',0)>0 for D in g.outgoing(B))]
print('S80 non-MOR entries with downstream ships', len(others), 'ok without ship term', sum(1 for k in others if abs(pred(*k)-idx.get(k,{}).get('prev',0.0))<0.0006))
