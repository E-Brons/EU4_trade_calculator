"""R11 Q2: protect-mission fleets that contain non-light ship types: are those ships counted in light_ship/ship_power?"""
import sys,json; sys.path.insert(0,'scripts/research')
exec(open('scripts/research/r11_r14_fleetflags.py').read().split("unique=0")[0])
tn=json.load(open('data/tradenodes.json'))['nodes']
for e in common.entries():
    if e['id'] not in('S79','S80'): continue
    order=[n['definitions'] for n in common.nodes(e)]; cs=common.block(e,'countries')
    ent={(t,n['definitions']):(x['light_ship'],x['ship_power']) for n in common.nodes(e) for t,x in n.items() if isinstance(x,dict) and 'light_ship' in x}
    for t,c in cs.items():
        if not isinstance(c,dict) or 'navy' not in c: continue
        nv=c['navy'] if isinstance(c['navy'],list) else [c['navy']]
        for f in nv:
            m=f.get('mission')
            if not(isinstance(m,dict) and isinstance(m.get('protect_mission'),dict)): continue
            sh=f['ship'] if isinstance(f['ship'],list) else [f['ship']]
            ty=Counter(s['type'] for s in sh)
            if set(ty)-set(BASE):
                node=order[int(m['protect_mission']['node'])-1]
                print(e['id'],t,node,f['name'],dict(ty),'on_my_way' in m['protect_mission'],'entry (light_ship,ship_power)=',ent.get((t,node)))
print('protect-mission nodes that are inland (all fleets, all 4 saves):',sorted({k[1] for sid,k,en,l,s in rows if tn[k[1]]['inland']}))
