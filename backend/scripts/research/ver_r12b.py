import sys; sys.path.insert(0, 'scripts/research')
from collections import Counter
from ver_common import *
ids=[i for i in ENT if i not in DUP]
tolC=Counter(); resid=Counter(); n_=0; ex={}
for sid in ids:
    ns=nodes_of(sid); order=[n[0] for n in ns]
    inc={}
    for nid,raw,ents in ns:
        for i in lst(raw.get('incoming')):
            if isinstance(i,dict): inc.setdefault(nid,{}).setdefault(order[int(i['from'])-1],[]).append((fl(i['value']),fl(i.get('add'),0.0)))
    for nid,raw,ents in ns:
        t=[o['target'] for o in GRAPH.get(nid,{}).get('outgoing',[])]; out=fl(raw.get('outgoing'))
        if not t or out is None: continue
        L=[inc.get(x,{}).get(nid) for x in t]
        if any(l is None or len(l)!=1 for l in L): continue
        L=[l[0] for l in L]; S=sum(v for v,a in L); A=sum(a for v,a in L); k=len(t)
        d=S-out; n_+=1
        for name,tol in (('abs0.001',0.001),('abs0.0015k',0.0015*k),('abs0.01',0.01),('abs0.05',0.05),('abs0.1',0.1),('rel0.5%',0.005*out),('rel1%',0.01*out),('rel2%',0.02*out)):
            tolC[name]+= abs(d)<=tol+1e-9
        w=[float(x) for x in lst(raw.get('steer_power'))]
        if A==0 and len(w)==k:
            r=(S)-out*sum(w)   # residual w.r.t. weights actually stored
            resid['n']+=1; resid['|r|<=0.001k']+= abs(r)<=0.001*k+1e-9; resid['|r|<=0.002k']+= abs(r)<=0.002*k+1e-9
            resid['|d|<=|out(1-sw)|+0.001k']+= abs(d)<= out*(1-sum(w))+0.001*k+1e-9
print('80 unique nodes',n_,dict(tolC)); print(dict(resid))
print({k: round(v/n_*100,1) for k,v in tolC.items()})

# tight bound incl. nodes with add: |S - A - out*sum(w)| <= tol*k
for tol in (0.001, 0.0015, 0.002):
    c=Counter()
    for sid in ids:
        ns=nodes_of(sid); order=[n[0] for n in ns]; inc={}
        for nid,raw,ents in ns:
            for i in lst(raw.get('incoming')):
                if isinstance(i,dict): inc.setdefault(nid,{}).setdefault(order[int(i['from'])-1],[]).append((fl(i['value']),fl(i.get('add'),0.0)))
        for nid,raw,ents in ns:
            t=[o['target'] for o in GRAPH.get(nid,{}).get('outgoing',[])]; out=fl(raw.get('outgoing')); w=[float(x) for x in lst(raw.get('steer_power'))]
            if not t or out is None or len(w)!=len(t): continue
            L=[inc.get(x,{}).get(nid) for x in t]
            if any(l is None or len(l)!=1 for l in L): continue
            L=[l[0] for l in L]; S=sum(v for v,a in L); A=sum(a for v,a in L); k=len(t)
            key='add' if A>0 else 'noadd'
            c[key+'_n']+=1; c[key+'_ok']+= abs(S-A-out*sum(w))<=tol*k+1e-9
    print('tight bound tol',tol,dict(c))
