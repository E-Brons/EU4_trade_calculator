"""R14 Q2: real max_demand values to design the additive-vs-multiplicative away-penalty pair."""
import sys,json,statistics; sys.path.insert(0,'scripts/research')
import common
E={x['id']:x for x in common.entries()}
def mds(sid,tag):
    return {n['definitions']:n[tag] for n in common.nodes(E[sid]) if isinstance(n.get(tag),dict)}
for sid,tag in (('S02','ENG'),('S04','CAS'),('S06','HAB'),('S14','TUR'),('S79','TUR'),('S80','TUR')):
    d=mds(sid,tag); v=[c['max_demand'] for c in d.values() if 'max_demand' in c]
    print(sid,tag,E[sid]['date'],'max_demand over',len(v),'nodes: min',min(v),'median',round(statistics.median(v),3),'max',max(v))
print('--- the draft pairs')
for sid,tag,node in (('S02','ENG','genua'),('S04','CAS','tunis')):
    md=mds(sid,tag)[node]['max_demand']; print(f'{sid} {tag} {node}: C md={md}; multiplicative B md={round(md*0.5,4)}; additive B md={round(md-0.5,4)}; difference {round(md*0.5-(md-0.5),4)}')
print('--- TUR S79 passive/non-collecting nodes with md>=2.0 (candidates where hypotheses differ by >0.5 in md)')
d=mds('S79','TUR'); rows=[(n,c['max_demand'],c.get('province_power'),'type' in c,'total' in c,c.get('has_capital')) for n,c in d.items() if c.get('max_demand',0)>=2.0]
for r in sorted(rows,key=lambda r:-r[1])[:8]: print(r, 'mult->',round(r[1]*.5,3),'add->',round(r[1]-.5,3))
# corpus: start saves vs ticked: how high max_demand is overall
allv={}
for sid in E:
    v=[]
    for n in common.nodes(E[sid]):
        c=n.get(E[sid]['tag'])
        if isinstance(c,dict) and 'max_demand' in c: v.append(c['max_demand'])
    allv[sid]=(min(v),max(v))
print('player max_demand max per save (top 8):',sorted(((v[1],k) for k,v in allv.items()),reverse=True)[:8])
print('1444 saves: highest player max_demand:',max(v[1] for k,v in allv.items() if E[k]['date']=='1444.11.11'))
