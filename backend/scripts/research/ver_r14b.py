import sys,re,tempfile,pathlib
sys.path.insert(0,'scripts/research')
import common
from app.trade import corpus, savefile
from collections import Counter
A=common.as_list
E={x['id']:x for x in common.entries()}
# six named players: envoys/placed
for sid in ('S02','S03','S04','S05','S06','S14'):
    e=E[sid]; nodes=common.nodes(e); cs=common.block(e,'countries')
    placed=sum(1 for n in nodes for k,c in n.items() if k==e['tag'] and isinstance(c,dict) and c.get('has_trader'))
    m=cs[e['tag']].get('merchants'); print(sid,e['tag'],'envoys',len(A(m.get('envoy'))),'placed',placed)
# md extremes among players
ex=[]
for sid,e in E.items():
    if e['date']!='1444.11.11': continue
    for n in common.nodes(e):
        c=n.get(e['tag'])
        if isinstance(c,dict) and 'max_demand' in c: ex.append((float(c['max_demand']),sid,e['tag'],n['definitions']))
ex.sort(); print('lowest',ex[:3],'highest',ex[-3:])
# count field location
rows=[]
for sid in ('S02','S03','S14'):
    e=E[sid]
    with tempfile.TemporaryDirectory() as tmp:
        p=corpus.locate(e,pathlib.Path(tmp)); g=savefile.read_save_text(p).gamestate
    print(sid,[(m.start(),m.group(0)) for m in re.finditer(r'(?m)^\s*multiplayer_random_(seed|count)\s*=\s*\d+',g)][:4])
cnt=[]
for sid,e in E.items():
    if e['date']!='1444.11.11': continue
    with tempfile.TemporaryDirectory() as tmp:
        p=corpus.locate(e,pathlib.Path(tmp)); g=savefile.read_save_text(p).gamestate
    m=re.search(r'(?m)^multiplayer_random_count=(\d+)',g); cnt.append((int(m.group(1)),sid))
cnt.sort(); print('count lowest',cnt[:2],'highest',cnt[-3:])
