"""R11 Q1/Q4: which protect-mission fleets are counted in the node entry? Subset-fit per (tag,node), then compare fleet attributes."""
import sys, json, itertools
sys.path.insert(0,'scripts/research')
import common
from collections import Counter, defaultdict
BASE={k:v['trade_power'] for k,v in json.load(open('data/game/light_ships.json'))['ships'].items()}
rows=[]
for e in common.entries():
    if e['id'] not in ('S79','S80'): continue
    nodes=common.nodes(e); order=[n['definitions'] for n in nodes]
    ent={}
    for n in nodes:
        for tag,c in n.items():
            if isinstance(c,dict) and c.get('light_ship'): ent[(tag,n['definitions'])]=(int(c['light_ship']),float(c['ship_power']))
    cs=common.block(e,'countries')
    fl=defaultdict(list)
    for tag in {t for t,_ in ent}|{t for t in cs if isinstance(cs[t],dict) and 'navy' in cs[t]}:
        c=cs[tag]
        if not isinstance(c,dict): continue
        nv=c.get('navy',[]); nv=nv if isinstance(nv,list) else [nv]
        for f in nv:
            m=f.get('mission')
            if not(isinstance(m,dict) and isinstance(m.get('protect_mission'),dict)): continue
            pm=m['protect_mission']; name=order[int(pm['node'])-1]
            sh=f.get('ship',[]); sh=sh if isinstance(sh,list) else [sh]
            lt=Counter(s['type'] for s in sh if s['type'] in BASE)
            fl[(tag,name)].append(dict(fleet=f.get('name'),lt=lt,n=sum(lt.values()),base=sum(BASE[t]*k for t,k in lt.items()),
                loc=f.get('location'),at_sea=f.get('at_sea'),has_path='path' in f,on_my_way=pm.get('on_my_way'),
                cyc=pm.get('current_cycle_begin'),tgt=pm.get('current_route_target'),route_len=(len(pm['trade']) if isinstance(pm.get('trade'),list) else 1),
                mp=f.get('movement_progress'),afl=f.get('active_fraction_last_month'),keys=sorted(set(f)-{'ship','id','name'})))
    # restrict to light fleets only
    for key,lst in fl.items():
        lst=[f for f in lst if f['n']>0]
        en=ent.get(key)
        target=en[0] if en else 0
        sols=[]
        for r in range(len(lst)+1):
            for sub in itertools.combinations(range(len(lst)),r):
                if sum(lst[i]['n'] for i in sub)==target: sols.append(sub)
        rows.append((e['id'],key,en,lst,sols))
unique=0; amb=0; none=0
cnt=Counter()
for sid,key,en,lst,sols in rows:
    if len(sols)==1:
        unique+=1
        for i,f in enumerate(lst):
            counted = i in sols[0]
            cnt[(counted,f['on_my_way'])]+=1
            if not (counted==True and f['on_my_way']==False) and not(counted==False and f['on_my_way']==True): print(sid,key,'counted',counted,{k:v for k,v in f.items() if k not in('keys','lt')},dict(f['lt']))
    elif not sols: none+=1; print('NOFIT',sid,key,en)
    else: amb+=1
print('unique',unique,'ambiguous',amb,'nofit',none); print(cnt)

print('--- location test')
tn=json.load(open('data/tradenodes.json'))['nodes']
mem={k:set(v['member_provinces']) for k,v in tn.items()}
c2=Counter()
for sid,key,en,lst,sols in rows:
    if len(sols)!=1: continue
    for i,f in enumerate(lst):
        counted=i in sols[0]
        c2[(counted, f['loc'] in mem[key[1]], f['has_path'], f['on_my_way'])]+=1
for k,v in sorted(c2.items(),key=str): print('counted',k[0],'loc_in_node',k[1],'has_path',k[2],'on_my_way',k[3],':',v)
print('inland nodes with ship entries:', {k[1] for sid,k,en,l,s in rows if en and tn[k[1]]['inland']})
