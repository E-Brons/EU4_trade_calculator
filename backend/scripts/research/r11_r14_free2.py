"""R14 Q1: is envoy.action==2 <=> placed (has_trader node)? free merchants = envoys without `action`."""
import sys,json; sys.path.insert(0,'scripts/research')
import common
from common import as_list
from collections import Counter
agree=Counter(); sample=[]
for e in common.entries():
    if e['date']!='1444.11.11': continue
    nodes=common.nodes(e); cs=common.block(e,'countries'); placed=Counter()
    for n in nodes:
        for t,c in n.items():
            if isinstance(c,dict) and c.get('has_trader'): placed[t]+=1
    for t,c in cs.items():
        if not isinstance(c,dict) or not (c.get('num_of_cities') or 0): continue
        m=c.get('merchants'); en=as_list(m.get('envoy')) if isinstance(m,dict) else []
        a2=sum(1 for x in en if x.get('action')==2)
        agree[a2==placed[t]]+=1
        if a2!=placed[t] and len(sample)<5: sample.append((e['id'],t,len(en),a2,placed[t]))
        if t==e['tag']: print(e['id'],t,'envoys',len(en),'action==2:',a2,'placed(has_trader nodes):',placed[t],'free(no action):',len(en)-a2)
print('country-saves where (#envoy action==2) == (#nodes with has_trader):',dict(agree)); print(sample)
