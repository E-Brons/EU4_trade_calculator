"""R11 verification part 3: quoted fleet names/blocks, on_my_way values, 4-fleet comparison, U01/U02 identity, start saves have no missions."""
import sys, json, pickle
sys.path.insert(0,'scripts/research')
import common
from collections import Counter, defaultdict
A=common.as_list
E={x['id']:x for x in common.entries()}
BASE=set(json.load(open('data/game/light_ships.json'))['ships'])

def fleets(cs,tag):
    return [f for f in A(cs[tag].get('navy')) if isinstance(f,dict)]
# (a) BLG S79 venice, YUE S80 canton
for sid,tag in (('S79','BLG'),('S80','YUE')):
    cs=common.block(E[sid],'countries'); order=[n['definitions'] for n in common.nodes(E[sid])]
    for f in fleets(cs,tag):
        m=f.get('mission'); pm=m.get('protect_mission') if isinstance(m,dict) else None
        if pm and order[int(pm['node'])-1] in ('venice','canton'):
            print(sid,tag,repr(f['name']),order[int(pm['node'])-1],dict(Counter(s['type'] for s in A(f.get('ship')) if isinstance(s,dict))))
# (b) TUR fleets without mission S79
cs=common.block(E['S79'],'countries')
print('TUR S79 fleets without protect mission:')
for f in fleets(cs,'TUR'):
    m=f.get('mission'); pm=m.get('protect_mission') if isinstance(m,dict) else None
    if not pm: print('  ',repr(f['name']),'mission keys:',list(m) if isinstance(m,dict) else m,dict(Counter(s['type'] for s in A(f.get('ship')) if isinstance(s,dict))))
# (d) raw Basra Trade Fleet mission block
for f in fleets(cs,'TUR'):
    if f['name']=='Basra Trade Fleet': print('Basra mission:',f['mission'])
# (k) on_my_way values + four fleets
vals=Counter(); four={}; cnt_stats=defaultdict(list)
four_names={('S79','C03','1st Fleet'),('S79','C03','9th Fleet'),('S79','TUR','Kizildeniz'),('S79','TUR','Karadeniz')}
for sid in ('S79','S80'):
    cs=common.block(E[sid],'countries')
    for tag,c in cs.items():
        if not isinstance(c,dict): continue
        for f in fleets(cs,tag):
            m=f.get('mission'); pm=m.get('protect_mission') if isinstance(m,dict) else None
            if not pm: continue
            if not any(s.get('type') in BASE for s in A(f.get('ship')) if isinstance(s,dict)): continue
            vals[(sid,repr(pm.get('on_my_way','<absent>')))]+=1
            rec=dict(mp=f.get('movement_progress'),path='path' in f,cyc=pm.get('current_cycle_begin'),name=f['name'],tag=tag,sid=sid,keys=sorted(f))
            cnt_stats['all'].append(rec)
print('on_my_way values (fleets with light ships):',dict(vals))
sel=[r for r in cnt_stats['all'] if (r['tag'],r['name'].replace('�','')[:9]) in {('C03','1st Fleet'),('C03','9th Fleet'),('TUR','K\x00'[:0]+'Kizildene'[:0])} ]
for r in cnt_stats['all']:
    if (r['sid']=='S79' and r['tag']=='C03' and r['name'] in ('1st Fleet','9th Fleet')) or (r['sid']=='S79' and r['tag']=='TUR' and (r['name'].startswith('K') and ('ldeniz' in r['name'] or 'radeniz' in r['name']))):
        print('FOUR',r['tag'],r['name'],'mp',r['mp'],'path',r['path'],'cycle',r['cyc'])
mps=[float(r['mp']) for r in cnt_stats['all'] if r['mp'] is not None and r['sid']=='S79']
print('S79 movement_progress over all light fleets: n',len(mps),'range',min(mps),max(mps),' with path:',sum(1 for r in cnt_stats['all'] if r['sid']=='S79' and r['path']))
cyc=Counter(r['cyc'] for r in cnt_stats['all'] if r['sid']=='S79'); print('cycle values S79',dict(cyc))
# (f) identity of U01/U02
for a,b in (('S79','U02'),('S80','U01')):
    ta=common.block(E[a],'trade'); tb=common.block(E[b],'trade')
    print(a,b,'trade trees equal:',ta==tb)
    ca=common.block(E[a],'countries'); cb=common.block(E[b],'countries')
    print('  countries equal:',ca==cb)
# (g) start saves: any mission on any fleet; light_ship in trade
bad=Counter(); n=0
for sid,e in E.items():
    if sid in ('S79','S80','U01','U02'): continue
    cs=common.block(e,'countries'); n+=1
    for tag,c in cs.items():
        if not isinstance(c,dict): continue
        for f in A(c.get('navy')):
            if isinstance(f,dict) and 'mission' in f: bad[sid]+=1
print('start saves checked',n,'fleets with mission:',dict(bad))
