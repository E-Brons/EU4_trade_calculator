"""R11 Q3: do fleets of ratio!=1 entries carry a leader / flagship? (country.navy[].leader, .flagship?)"""
import sys,pickle; sys.path.insert(0,'scripts/research')
exec(open('scripts/research/r11_r14_fleetflags.py').read().split("unique=0")[0])
per=pickle.load(open('/tmp/eu4research/cache/r11_ratio.pkl','rb'))
ratio={(sid,tag,node):r for (sid,tag),v in per.items() for node,r,n,sp in v}
fk=Counter(); res=Counter(); sample=[]
for e in common.entries():
    if e['id'] not in ('S79','S80'): continue
    order=[n['definitions'] for n in common.nodes(e)]
    cs=common.block(e,'countries')
    for (sid,tag,node),r in ratio.items():
        if sid!=e['id']: continue
        nv=cs[tag]['navy']; nv=nv if isinstance(nv,list) else [nv]
        fl=[f for f in nv if isinstance(f.get('mission'),dict) and isinstance(f['mission'].get('protect_mission'),dict) and order[int(f['mission']['protect_mission']['node'])-1]==node and 'on_my_way' in f['mission']['protect_mission']]
        has_leader=any('leader' in f for f in fl)
        res[(r!=1.0,has_leader)]+=1
        ship_keys=set()
        for f in fl:
            for s in (f['ship'] if isinstance(f['ship'],list) else [f['ship']]): ship_keys|=set(s)
        fk[(r!=1.0)]+=0
        if r!=1.0: sample.append((sid,tag,node,r,[ (f['name'],'leader' in f) for f in fl], sorted(ship_keys)))
print('(ratio!=1, any fleet with leader):',res)
for s in sample: print(s)
