import sys, tempfile; sys.path.insert(0, 'scripts/research')
from collections import Counter, defaultdict
from pathlib import Path
from ver_common import *
# C-04 multisets S80
ms=defaultdict(Counter)
for nid,raw,ents in nodes_of('S80'):
    for t,e in ents.items():
        if 'add' in e and 'type' in e: ms[t][round(e['add'],3)]+=1
for t in ('GBR','TUR','C05','SUN','SPA','C03'):
    print(t,dict(sorted(ms[t].items(),reverse=True)), 'ratio max/own', sorted({round(max(ms[t])/a,2) for a in ms[t]}))
# TUR same add in nodes with val 189 and 619
for nid,raw,ents in nodes_of('S80'):
    e=ents.get('TUR')
    if e and 'add' in e: print('  TUR',nid,'add',e['add'],'val',e.get('val'))
# SCA row
for nid,raw,ents in nodes_of('S80'):
    if nid=='carribean_trade': print('SCA',ents.get('SCA'))
# C05 k at nodes
for nid,raw,ents in nodes_of('S80'):
    e=ents.get('C05')
    if e and 'add' in e: print('  C05',nid,'add',e['add'],'steer_power',e.get('steer_power'))
# Q5: nodes >=2 links with no type/add entry
for label,ids in (('start',STARTS),('played',['S79','S80'])):
    c=Counter()
    for sid in ids:
        for nid,raw,ents in nodes_of(sid):
            k=len(GRAPH.get(nid,{}).get('outgoing',[])); w=[float(x) for x in lst(raw.get('steer_power'))]
            if k>=2 and len(w)==k and fl(raw.get('outgoing'),0)>0 and not any(('type' in e or 'add' in e) for e in ents.values()):
                c['n']+=1
                if max(w)-min(w)<1e-9: c['equal']+=1
                elif w[0]>0.999 and sum(w[1:])<1e-9: c['all_first']+=1
                else: c['other']+=1
    print('Q5',label,dict(c))
# weight sums
# steering text grep in S80 gamestate
from app.trade import savefile, corpus
with tempfile.TemporaryDirectory() as tmp:
    p=corpus.locate(ENT['S80'],Path(tmp)); st=savefile.read_save_text(p)
    g=st.gamestate; print('S80 gamestate chars',len(g),'bytes',len(g.encode()),'count steering',g.count('steering'),'count trade_steering',g.count('trade_steering'))
