"""R11: per save, per country: trade-node ship entries vs navy fleets with protect_mission. Prints a report; caches rows in /tmp/eu4research/cache/r11_rows.pkl"""
import sys, json, pickle
sys.path.insert(0,'scripts/research')
import common
from collections import Counter, defaultdict
LIGHT={'barque','caravel','early_frigate','frigate','heavy_frigate','great_frigate'}
rows=[]
for e in common.entries():
    nodes=common.nodes(e)
    order=[n['definitions'] for n in nodes]
    ent=[]
    for n in nodes:
        for tag,c in n.items():
            if isinstance(c,dict) and len(tag)<=4 and tag.upper()==tag and c.get('light_ship'):
                ent.append((n['definitions'],tag,int(c['light_ship']),float(c.get('ship_power',0))))
    if not ent: 
        rows.append((e['id'],None)); continue
    tags={t for _,t,_,_ in ent}
    cs=common.block(e,'countries')
    out={}
    for t in tags:
        c=cs[t]; nv=c.get('navy',[]); nv=nv if isinstance(nv,list) else [nv]
        fl=[]
        for f in nv:
            sh=f.get('ship',[]); sh=sh if isinstance(sh,list) else [sh]
            m=f.get('mission'); node=None
            if isinstance(m,dict) and isinstance(m.get('protect_mission'),dict): node=m['protect_mission'].get('node')
            fl.append((node,Counter(s['type'] for s in sh),f.get('name')))
        out[t]=dict(fleets=fl, nps=c.get('num_ships_protecting_trade'), trade_keys=[k for k in c if 'trade' in k and 'merch' not in k])
    rows.append((e['id'],dict(ent=ent,out=out,order=order,date=e['date'])))
pickle.dump(rows,open('/tmp/eu4research/cache/r11_rows.pkl','wb'))
for sid,r in rows:
    if r is None: continue
    print(sid, r['date'], 'entries',len(r['ent']),'tags',sorted(r['out']))
    for t,o in r['out'].items():
        miss=[(n,c) for n,c,_ in o['fleets'] if n is not None]
        print('   ',t,'nps',o['nps'],'fleets',len(o['fleets']),'with protect',len(miss), 'light_ship total', sum(l for _,tt,l,_ in r['ent'] if tt==t))
