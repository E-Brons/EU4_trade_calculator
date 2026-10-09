"""R04 Q6: receivers that neither steer nor collect; is their effective power inside pull_power? (R03 rule: steer, or not collecting here but collecting downstream)"""
import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, collections, functools
from app.trade import game_data
g=game_data.graph()
rows,nodes=fl.load()
nidx={(n['sid'],n['definitions']):n for n in nodes}
@functools.lru_cache(None)
def down(n):
    s=set()
    for t in g.outgoing(n): s.add(t); s|=down(t)
    return frozenset(s)
bys=collections.defaultdict(list)
for r in rows:
    if set(r)-{'max_demand','sid','node','tag','date'}: bys[r['sid']].append(r)
tot=0; bad=[]; recv_stats=collections.Counter(); recv_cases=[]
for sid,E in bys.items():
    coll=collections.defaultdict(set)
    for r in E:
        if 'total' in r: coll[r['tag']].add(r['node'])
    pernode=collections.defaultdict(list)
    for r in E: pernode[r['node']].append(r)
    for node,lst in pernode.items():
        n=nidx[(sid,node)]
        if n.get('pull_power') is None: continue
        tot+=1; pull=0.0
        for r in lst:
            eff=r.get('val',0)-r.get('t_out',0)+r.get('t_in',0)
            collhere='total' in r; steer='type' in r
            dc=bool(coll.get(r['tag'],set())&down(node))
            if steer or (not collhere and dc): pull+=eff
            if r.get('t_in',0)>0 and not collhere and not steer:
                recv_cases.append((sid,node,r['tag'],dc,round(eff,3)))
        d=n['pull_power']-pull
        if abs(d)>0.0105: bad.append((sid,node,round(d,3)))
print('nodes with pull_power', tot, 'mismatch', len(bad)); print(bad)
c=collections.Counter((dc) for *_,dc,_ in recv_cases)
print('non-collecting non-steering receivers (entries):', len(recv_cases), ' with downstream collection by the rule:', c)
# among those without downstream collection: do their nodes match?
badn=set((s,n) for s,n,_ in bad)
nd=[x for x in recv_cases if not x[3]]
print('receivers without downstream collection:', len(nd), ' of which in a mismatching node:', sum(1 for x in nd if (x[0],x[1]) in badn))
print(collections.Counter((x[0],x[2]) for x in nd).most_common(10))

print('=== downstream steering hypothesis')
steer_nodes=collections.defaultdict(lambda: collections.defaultdict(set))
for sid,E in bys.items():
    for r in E:
        if 'type' in r: steer_nodes[sid][r['tag']].add(r['node'])
res=collections.Counter()
for sid,node,tag,dc,eff in nd:
    ds = bool(steer_nodes[sid].get(tag,set()) & down(node))
    counted = (sid,node) in badn
    res[(ds, counted)]+=1
    if ds or counted: print(sid,node,tag,'downstream steer',ds,'counted in pull',counted, 'eff',eff)
print(dict(res))

print('=== generalised rule: steer here, or (not collecting here and (collects or steers downstream))')
tot=0; bad2=[]; changed=0
for sid,E in bys.items():
    coll=collections.defaultdict(set)
    for r in E:
        if 'total' in r: coll[r['tag']].add(r['node'])
    pernode=collections.defaultdict(list)
    for r in E: pernode[r['node']].append(r)
    for node,lst in pernode.items():
        n=nidx[(sid,node)]
        if n.get('pull_power') is None: continue
        tot+=1; pull=0.0; pull0=0.0
        for r in lst:
            eff=r.get('val',0)-r.get('t_out',0)+r.get('t_in',0)
            collhere='total' in r; steer='type' in r
            dc=bool(coll.get(r['tag'],set())&down(node)); ds=bool(steer_nodes[sid].get(r['tag'],set())&down(node))
            if steer or (not collhere and dc): pull0+=eff
            if steer or (not collhere and (dc or ds)): pull+=eff
        if abs(pull-pull0)>1e-9: changed+=1
        if abs(n['pull_power']-pull)>0.0105: bad2.append((sid,node,round(n['pull_power']-pull,3)))
print('nodes', tot, 'mismatch generalised', len(bad2), bad2, ' nodes whose prediction changes vs R03 rule:', changed)
