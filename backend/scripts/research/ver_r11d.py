"""R11 verification part 4: the 11th fleet without on_my_way; exact (tag,node) pair counts of C-09."""
import sys, json
sys.path.insert(0,'scripts/research')
import common
from collections import Counter, defaultdict
A=common.as_list
E={x['id']:x for x in common.entries()}
BASE={k:v['trade_power'] for k,v in json.load(open('data/game/light_ships.json'))['ships'].items()}
for sid in ('S79','S80'):
    nodes=common.nodes(E[sid]); order=[n['definitions'] for n in nodes]; cs=common.block(E[sid],'countries')
    ent={}
    for n in nodes:
        for k,c in n.items():
            if isinstance(c,dict) and 2<=len(k)<=4 and k.upper()==k and 'light_ship' in c: ent[(k,n['definitions'])]=(int(c['light_ship']),float(c['ship_power']))
    by=defaultdict(list)
    for tag,c in cs.items():
        if not isinstance(c,dict): continue
        for f in A(c.get('navy')):
            if not isinstance(f,dict): continue
            m=f.get('mission'); pm=m.get('protect_mission') if isinstance(m,dict) else None
            if not pm: continue
            by[(tag,order[int(pm['node'])-1])].append((f['name'],'on_my_way' in pm,Counter(s['type'] for s in A(f.get('ship')) if isinstance(s,dict))))
    keys=set(ent)|set(by)
    exact=0
    for k in keys:
        cnt=Counter()
        for _,_,c in by.get(k,[]): cnt.update({t:n for t,n in c.items() if t in BASE})
        l=sum(cnt.values()); b=sum(BASE[t]*n for t,n in cnt.items())
        if k in ent and ent[k][0]==l and abs(ent[k][1]-b)<1e-6: exact+=1
    print(sid,'pairs',len(keys),'exact (all fleets, f=1)',exact)
    if sid=='S80':
        for k,v in by.items():
            if k==('SPA','malacca'): print('SPA malacca fleets',v,'entry',ent.get(k))
    absent=[(k,n) for k,v in by.items() for n,has,c in v if not has and any(t in BASE for t in c)]
    print(sid,'light fleets lacking on_my_way',len(absent),absent)
