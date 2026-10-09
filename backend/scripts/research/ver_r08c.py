import sys, math; sys.path.insert(0, 'scripts/research')
from collections import Counter, defaultdict
from ver_common import *
from ver_r08b import inst, eff
def pred(ents,k,f):
    s=[0.0]*k
    for e in ents.values():
        if 'type' in e and 'val' in e:
            l=int(fl(e.get('steer_power'),0))
            if l<k: s[l]+=f(e)
    T=sum(s); return [x/T for x in s] if T else None
def rmse(p,w): return [(a-b)**2 for a,b in zip(p,w)]
for sid in ('S79','S80'):
    amax=defaultdict(float)
    for nid,raw,ents in nodes_of(sid):
        for t,e in ents.items():
            if 'add' in e: amax[t]=max(amax[t],e['add'])
    c=Counter(); se=defaultdict(list); allc=Counter(); allse=[]
    for s_,nid,raw,ents,k,w in inst([sid]):
        st={t:e for t,e in ents.items() if 'type' in e and 'val' in e}
        f_add=lambda e: 0.0
        def with_a(e):
            t=[t for t,x in st.items() if x is e][0]; return eff(e)*amax.get(t,0.0)
        p=pred(ents,k,with_a)
        if p is not None: allc['n']+=1; allc['ok']+= all(abs(a-b)<=0.0011 for a,b in zip(p,w)); allse+=rmse(p,w)
        clean=all(('add' in e and abs(e['add']-amax[t])<1e-9) for t,e in st.items())
        if not clean or p is None: continue
        c['n']+=1
        for name,f in (('eff*add',lambda e:eff(e)*e['add']),('val*add',lambda e:fl(e['val'])*e['add']),('eff',eff)):
            q=pred(ents,k,f); c[name]+= all(abs(a-b)<=0.0011 for a,b in zip(q,w)); se[name]+=rmse(q,w)
        if nid in ('james_bay','persia','california','mississippi_river','lahore','alexandria','gujarat'): print('   ',sid,nid,[round(x,4) for x in p],w)
    print(sid,'clean subset',dict(c),{k:round(math.sqrt(sum(v)/len(v)),4) for k,v in se.items()},'| all steerer nodes',dict(allc),round(math.sqrt(sum(allse)/len(allse)),4))

print('--- per-node max-error RMSE (author definition)')
for sid in ('S80',):
    amax=defaultdict(float)
    for nid,raw,ents in nodes_of(sid):
        for t,e in ents.items():
            if 'add' in e: amax[t]=max(amax[t],e['add'])
    for nm in ('eff*add','eff'):
        se=[]
        for s_,nid,raw,ents,k,w in inst([sid]):
            st={t:e for t,e in ents.items() if 'type' in e and 'val' in e}
            if not all(('add' in e and abs(e['add']-amax[t])<1e-9) for t,e in st.items()): continue
            q=pred(ents,k,(lambda e:eff(e)*e['add']) if nm=='eff*add' else eff)
            se.append(max(abs(a-b) for a,b in zip(q,w))**2)
        print(sid,nm,len(se),round(math.sqrt(sum(se)/len(se)),4))
se=[]
for sid in ('S79','S80'):
    amax=defaultdict(float)
    for nid,raw,ents in nodes_of(sid):
        for t,e in ents.items():
            if 'add' in e: amax[t]=max(amax[t],e['add'])
    for s_,nid,raw,ents,k,w in inst([sid]):
        q=pred(ents,k,lambda e: eff(e)*amax.get([t for t,x in ents.items() if x is e][0],0.0))
        if q: se.append(max(abs(a-b) for a,b in zip(q,w))**2)
print('all steerer nodes',len(se),round(math.sqrt(sum(se)/len(se)),4))
