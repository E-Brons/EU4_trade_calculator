"""Independent verification of R14 response_1 (facts of the matrix, free merchants, md values, seeds)."""
import sys, json, re, datetime
sys.path.insert(0,'scripts/research')
import common
from collections import Counter, defaultdict
A=common.as_list
E={x['id']:x for x in common.entries()}
TN=json.load(open('data/tradenodes.json'))['nodes']
def is_tag(k,v): return isinstance(v,dict) and 2<=len(k)<=4 and k.upper()==k and k!='PIR' or (isinstance(v,dict) and k=='PIR')
def ent(sid):
    nodes=common.nodes(E[sid]); d={}
    for n in nodes:
        for k,c in n.items():
            if isinstance(c,dict) and 2<=len(k)<=4 and k.upper()==k: d[(n['definitions'],k)]=c
    return nodes,d

print('--- graph')
print('out-degree distribution', Counter(len(v['outgoing']) for v in TN.values()))
for d in (0,2,3,4): print(d,'links:',sorted(k for k,v in TN.items() if len(v['outgoing'])==d) if d!=2 else sorted(k for k,v in TN.items() if len(v['outgoing'])==2)[:60])
for n in ('safi','tunis','alexandria','wien','ivory_coast','champagne','north_sea','english_channel'): print(n,[o['target'] for o in TN[n]['outgoing']])
# cross-check graph vs save incoming for S03
nodes,_=ent('S03'); order=[n['definitions'] for n in nodes]
rev=defaultdict(set)
for n in nodes:
    for i in A(n.get('incoming')):
        if isinstance(i,dict): rev[order[int(i['from'])-1]].add(n['definitions'])
bad=[k for k in TN if {o['target'] for o in TN[k]['outgoing']}!=rev.get(k,set())]
print('graph vs save incoming mismatches (S03):',bad)

print('--- S03 FRA/ENG/SCO facts')
nodes,d=ent('S03')
for (n,t),c in d.items():
    if t=='FRA' and (c.get('has_capital') or n in('english_channel',)): print('FRA',n,{k:c.get(k) for k in('has_capital','province_power','total','max_demand','has_trader','type')})
    if t=='SCO' and (c.get('has_capital') or n=='north_sea'): print('SCO',n,{k:c.get(k) for k in('has_capital','province_power','total','max_demand','has_trader','type')})
print('FRA traders:',[(n,c.get('type')) for (n,t),c in d.items() if t=='FRA' and c.get('has_trader')])
print('FRA at north_sea',d.get(('north_sea','FRA')))
nodes,d=ent('S02')
print('ENG home:',[(n,c.get('province_power'),c.get('total')) for (n,t),c in d.items() if t=='ENG' and c.get('has_capital')])
print('ENG traders:',[(n,c.get('type'),c.get('prev')) for (n,t),c in d.items() if t=='ENG' and c.get('has_trader')],'genua',d.get(('genua','ENG')))
nodes,d=ent('S04')
print('CAS home',[n for (n,t),c in d.items() if t=='CAS' and c.get('has_capital')],'tunis',d.get(('tunis','CAS')),'traders',[(n,c.get('type')) for (n,t),c in d.items() if t=='CAS' and c.get('has_trader')])
nodes,d=ent('S14')
print('TUR alexandria',d.get(('alexandria','TUR')))
nodes,d=ent('S05')
print('POR safi',d.get(('safi','POR')),'tunis',d.get(('tunis','POR')),'ivory_coast',d.get(('ivory_coast','POR')),'traders',[(n,c.get('type')) for (n,t),c in d.items() if t=='POR' and c.get('has_trader')])
nodes,d=ent('S06')
print('HAB wien',d.get(('wien','HAB')),'traders',[(n,c.get('type')) for (n,t),c in d.items() if t=='HAB' and c.get('has_trader')])
# ARA, SCO S03
for tag in('ARA','SCO'):
    nodes,d=ent('S03')
    print(tag,'home',[n for (n,t),c in d.items() if t==tag and c.get('has_capital')],'traders',[(n,c.get('type'),c.get('total') is not None) for (n,t),c in d.items() if t==tag and c.get('has_trader')],'genua',d.get(('genua',tag)))

print('--- countries facts')
for sid,tags in (('S03',['PRU','BRA','SCO','ARA','OPM']),('S06',['PRU','OPM']),('S62',['PRU','BRA'])):
    cs=common.block(E[sid],'countries'); nodes,d=ent(sid)
    for t in tags:
        c=cs.get(t)
        if c is None: print(sid,t,'NOT A KEY'); continue
        m=c.get('merchants'); en=A(m.get('envoy')) if isinstance(m,dict) else []
        hc=[n for (n,tt),cc in d.items() if tt==t and cc.get('has_capital')]
        print(sid,t,'cities',c.get('num_of_cities'),'envoys',len(en),'has_capital',hc,'traders',[(n,cc.get('type')) for (n,tt),cc in d.items() if tt==t and cc.get('has_trader')])

print('--- free merchants over 1444 start saves')
tot=0; eq=0; neq=[]; players=[]; more=Counter(); sco=None
for sid,e in E.items():
    if e['date']!='1444.11.11': continue
    nodes,d=ent(sid); cs=common.block(e,'countries')
    placed=Counter(t for (n,t),c in d.items() if c.get('has_trader'))
    for t,c in cs.items():
        if not isinstance(c,dict) or not (c.get('num_of_cities') or 0): continue
        m=c.get('merchants'); en=A(m.get('envoy')) if isinstance(m,dict) else []
        act=sum(1 for x in en if isinstance(x,dict) and x.get('action')==2)
        tot+=1
        if act==placed[t]: eq+=1
        else: neq.append((sid,t,act,placed[t],len(en)))
        if len(en)>placed[t]: more[sid]+=1
        if t==e['tag']: players.append((sid,t,len(en),placed[t]))
        if sid=='S03' and t=='SCO': sco=(len(en),placed[t])
print('country-saves with cities',tot,'action2==placed',eq,'differ',len(neq), [x for x in neq if x[1] in('CHT','MIS')][:4])
print('players with free merchant:',[p for p in players if p[2]>p[3]],'n players',len(players))
print('players without:',[p[1] for p in players if p[2]<=p[3]])
print('SCO S03 (envoys, placed)',sco,'S03 countries envoys>placed',more['S03'])
print('players (envoys,placed) dist',Counter((p[2],p[3]) for p in players))

print('--- md ranges of players at 1444')
rng=defaultdict(list)
for sid,e in E.items():
    if e['date']!='1444.11.11': continue
    nodes,d=ent(sid)
    for (n,t),c in d.items():
        if t==e['tag'] and 'max_demand' in c: rng[t].append(float(c['max_demand']))
allv=[v for l in rng.values() for v in l]
print('all players md range',min(allv),max(allv))
for t in('ENG','CAS','HAB','TUR'): print(t,min(rng[t]),max(rng[t]))
nodes,d=ent('S02'); print('ENG genua md',d[('genua','ENG')].get('max_demand'),'home md',[c.get('max_demand') for (n,t),c in d.items() if t=='ENG' and c.get('has_capital')])
nodes,d=ent('S04'); print('CAS tunis md',d[('tunis','CAS')].get('max_demand'))
for sid in('S79','S80'):
    nodes,d=ent(sid); tm=[(n,float(c['max_demand'])) for (n,t),c in d.items() if t=='TUR' and 'max_demand' in c]
    print(sid,'TUR md max',max(v for _,v in tm),Counter(round(v,3) for _,v in tm).most_common(3))
    if sid=='S79':
        for n in('african_great_lakes','kongo','zambezi','patagonia','amazonas_node','rio_grande','james_bay','california'):
            c=d.get((n,'TUR')); print('   ',n,c)
print('mult/add', 1.067*0.5,1.067-0.5,1.054*0.5,1.054-0.5, 2.11*.5, 2.11-.5)

print('--- seeds')
import tempfile
from app.trade import corpus, savefile
seeds={}
for sid,e in E.items():
    with tempfile.TemporaryDirectory() as tmp:
        p=corpus.locate(e,__import__('pathlib').Path(tmp)); txt=savefile.read_save_text(p)
    g=txt.gamestate
    s=re.search(r'(?m)^multiplayer_random_seed=(\d+)',g); c=re.search(r'(?m)^multiplayer_random_count=(\d+)',g)
    seeds[sid]=(int(s.group(1)) if s else None,int(c.group(1)) if c else None,e['date'])
    if sid=='S14':
        print('S14 decision_seed count',len(re.findall(r'decision_seed',g)),'\\bseed=',len(re.findall(r'(?<![_a-z])seed\s*=',g)))
st=[v for k,v in seeds.items() if E[k]['date']=='1444.11.11']
print('start saves',len(st),'distinct seeds',len({a for a,_,_ in st}),'counts',min(b for _,b,_ in st),max(b for _,b,_ in st),'distinct counts',len({b for _,b,_ in st}))
print('S02',seeds['S02'],'S03',seeds['S03'])
for k in('S79','S80','U01','U02'): print(k,seeds[k])
d0=seeds['S80'][1]-seeds['S79'][1]
days=(1682-1665)*365+(31+28+31+18)-(31+28+31+22)   # EU4 calendar: 365-day years
print('draw diff',d0,'EU4 days',days,'draws/day',d0/days)
