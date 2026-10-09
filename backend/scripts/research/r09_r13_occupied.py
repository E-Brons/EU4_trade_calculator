"""R13 Q6: occupied provinces (controller != owner, controller != REB): whose entry carries the power?"""
import sys,re,collections
sys.path.insert(0,'scripts/research')
import common
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
st=collections.Counter(); ex=[]
for e in common.entries():
    prov=common.block(e,'provinces'); nodes={n['definitions']:n for n in common.nodes(e)}
    byc=collections.defaultdict(float); byo=collections.defaultdict(float); occ=[]
    for pid,p in prov.items():
        if not isinstance(p,dict) or 'trade' not in p or p.get('trade_power') is None or not p.get('controller'): continue
        byc[(p['trade'],p['controller'])]+=p['trade_power']
        if p.get('owner'): byo[(p['trade'],p['owner'])]+=p['trade_power']
        if p.get('owner') and p['controller']!=p['owner'] and p['controller']!='REB' and p['trade_power']>0.01: occ.append(p)
    for p in occ:
        nid=p['trade']; n=nodes.get(nid,{}); 
        c=n.get(p['controller'],{}).get('province_power',0.0); o=n.get(p['owner'],{}).get('province_power',0.0)
        st['occupied provinces with power>0']+=1
        k=(nid,p['controller']); k2=(nid,p['owner'])
        okc=abs(c-byc[k])<0.0005*5+0.001; oko=abs(o-byo[k2])<0.0005*5+0.001
        st['controller entry == sum by controller']+=okc; st['ctrl FAIL in '+('played' if e['id'] in ('S79','S80','U01','U02') else 'start saves')]+= (not okc); st['occupied in '+('played' if e['id'] in ('S79','S80','U01','U02') else 'start saves')]+=1; st['owner entry == sum by owner (owner basis)']+=oko
        st['owner entry == sum by controller basis']+= abs(o-byc[k2])<0.0005*5+0.001
        if len(ex)<3 and e['id'] in('S79',): ex.append((e['id'],nid,p['owner'],p['controller'],p['trade_power'],'ctrl entry',c,'sum_ctrl',round(byc[k],3),'owner entry',o,'sum_ctrl(owner)',round(byc[k2],3)))
print(dict(st)); print(ex)
