"""R14 Q1: free merchants in the 1444 start saves: envoys (country.merchants.envoy) vs nodes with has_trader; and max_demand values for the away-penalty pair design."""
import sys,json; sys.path.insert(0,'scripts/research')
import common
from common import as_list
from collections import Counter
tag_has=Counter(); player_rows=[]; free=[]; envact=Counter()
for e in common.entries():
    if e['date']!='1444.11.11': continue
    nodes=common.nodes(e); cs=common.block(e,'countries')
    placed=Counter()
    for n in nodes:
        for t,c in n.items():
            if isinstance(c,dict) and c.get('has_trader'): placed[t]+=1
    for t,c in cs.items():
        if not isinstance(c,dict) or not (c.get('num_of_cities') or 0): continue
        m=c.get('merchants'); en=as_list(m.get('envoy')) if isinstance(m,dict) else []
        for x in en: envact[(x.get('action'),x.get('type'))]+=1
        if t==e['tag']: player_rows.append((e['id'],t,len(en),placed[t]))
        if len(en)>placed[t]: free.append((e['id'],t,len(en),placed[t]))
print('player countries (envoys, nodes with has_trader):',Counter((r[2],r[3]) for r in player_rows))
print('player countries with a free merchant:',[r for r in player_rows if r[2]>r[3]])
print('envoy (action,type) counts over all countries of the 35 start saves:',dict(envact))
print('countries(with cities) in S03 with envoys>placed:',[f for f in free if f[0]=='S03'][:20], 'n=',sum(1 for f in free if f[0]=='S03'))
