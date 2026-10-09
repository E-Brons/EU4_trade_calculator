"""R11 Q1/Q3/Q4: reconcile protect_mission fleets (country.navy[].mission.protect_mission.node, 1-based) with trade-node light_ship/ship_power."""
import sys, json, pickle
sys.path.insert(0,'scripts/research')
import common
from collections import Counter, defaultdict
BASE={k:v['trade_power'] for k,v in json.load(open('data/game/light_ships.json'))['ships'].items()}
if __name__=='__main__':
    res=[]
    for e in common.entries():
        if e['id'] not in ('S79','S80','U01','U02'): continue
        nodes=common.nodes(e); order=[n['definitions'] for n in nodes]
        ent={}
        for n in nodes:
            for tag,c in n.items():
                if isinstance(c,dict) and c.get('light_ship'):
                    ent[(tag,n['definitions'])]=(int(c['light_ship']),float(c['ship_power']))
        cs=common.block(e,'countries')
        fleets=defaultdict(list)   # (tag,node)->list of (fleetname, Counter types, ship dicts)
        tot_nps={}
        for tag in {t for t,_ in ent}:
            c=cs[tag]; tot_nps[tag]=c.get('num_ships_protecting_trade')
            nv=c.get('navy',[]); nv=nv if isinstance(nv,list) else [nv]
            for f in nv:
                m=f.get('mission')
                if not(isinstance(m,dict) and isinstance(m.get('protect_mission'),dict)): continue
                nid=int(m['protect_mission']['node']); name=order[nid-1]
                sh=f.get('ship',[]); sh=sh if isinstance(sh,list) else [sh]
                fleets[(tag,name)].append(dict(fleet=f.get('name'),types=Counter(s['type'] for s in sh),loc=f.get('location'),at_sea=f.get('at_sea'),mp=f.get('movement_progress')))
        res.append((e['id'],ent,fleets,tot_nps))
        print('==',e['id'])
        exact=0; bad=[]
        for key in sorted(set(ent)|set(fleets)):
            fl=fleets.get(key,[])
            types=Counter();
            for f in fl: types.update(f['types'])
            light={t:n for t,n in types.items() if t in BASE}
            nl=sum(light.values()); pb=sum(BASE[t]*n for t,n in light.items())
            en=ent.get(key)
            ok = en is not None and en[0]==nl and abs(en[1]-pb)<1e-6
            if ok: exact+=1
            else: bad.append((key,en,nl,pb,light,[(f['fleet'],dict(f['types']),f['at_sea']) for f in fl]))
        print('fleet-node pairs',len(set(ent)|set(fleets)),'exact (count and base power)',exact,'mismatch',len(bad))
        for b in bad: print('  ',b)
    pickle.dump(res,open('/tmp/eu4research/cache/r11_reconcile.pkl','wb'))
