"""R09 Q2: already_sent vs province_power/5 x number of upstream nodes (graph in-degree)."""
import sys,re,collections,math
sys.path.insert(0,'scripts/research')
import common
from app.parsing.tradenodes import load_trade_graph
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
g=load_trade_graph()
indeg=collections.Counter()
for nid in g.nodes:
    for o in g.outgoing(nid): indeg[o]+=1
fx=lambda x: math.trunc(x*1000+1e-9)/1000
st=collections.Counter(); ex=[]; ks=collections.Counter()
for e in common.entries():
    for n in common.nodes(e):
        nid=n['definitions']
        for t,v in n.items():
            if not(TAG.match(t) and isinstance(v,dict)): continue
            pp=v.get('province_power',0.0)
            if 'already_sent' in v:
                st['with already_sent']+=1; a=v['already_sent']
                k=a/(pp*0.2) if pp>0 else None
                ks[round(k,2) if k else k]+=1
                if abs(a-fx(pp*0.2*indeg[nid]))<=0.0015*max(1,indeg[nid]): st['already_sent == pp/5 * indegree']+=1
                elif len(ex)<6: ex.append((e['id'],nid,t,a,pp,indeg[nid]))
                if abs(a-fx(pp*0.2*sum(1 for o in g.nodes if nid in g.outgoing(o))))<=0.0015: st['dup']+=0
            elif pp>0:
                st['province_power>0 without already_sent']+=1
                if pp>=10: st['  of which pp>=10']+=1
print(dict(st)); print(ex); print('k = already_sent/(0.2*province_power) histogram',ks.most_common(10))
print('indegree histogram',collections.Counter(indeg.values()), 'nodes with indegree 0',sum(1 for n in g.nodes if indeg[n]==0))
