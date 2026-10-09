"""R11 Q3: which entries have ship multiplier != 1, and what do they share."""
import sys,pickle; sys.path.insert(0,'scripts/research')
import common
from collections import Counter
per=pickle.load(open('/tmp/eu4research/cache/r11_ratio.pkl','rb'))
for e in common.entries():
    if e['id'] not in ('S79','S80'): continue
    nodes={n['definitions']:n for n in common.nodes(e)}
    tab=[]
    for (sid,tag),v in per.items():
        if sid!=e['id']: continue
        for node,r,n,sp in v:
            c=nodes[node][tag]
            tab.append((r!=1.0,node,tag,r,n,nodes[node].get('trade_company_region'),c.get('has_capital'),c.get('has_trader'),'type' in c,'total' in c,c.get('max_demand'),[ (m['key'],m.get('power'),m.get('power_modifier')) for m in (c['modifier'] if isinstance(c.get('modifier'),list) else [c['modifier']] if c.get('modifier') else [])]))
    print('==',e['id'],'entries',len(tab),'ratio!=1:',sum(1 for t in tab if t[0]))
    for t in tab:
        if t[0]: print('  ',t[1:])
    print('  trade_company_region among ratio!=1:',Counter(t[5] for t in tab if t[0]),'among ratio==1:',Counter(t[5] for t in tab if not t[0]))
    print('  role among ratio!=1 (capital,trader,steer,collect):',Counter(t[6:10] for t in tab if t[0]))
    print('  role among ratio==1:',Counter(t[6:10] for t in tab if not t[0]))
