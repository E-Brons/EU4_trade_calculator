import sys; sys.path.insert(0, 'scripts/research')
from collections import Counter
from ver_common import *
def eff(e): return fl(e.get('val'),0)-fl(e.get('t_out'),0)+fl(e.get('t_in'),0)
def inst(ids):
    for sid in ids:
        for nid,raw,ents in nodes_of(sid):
            k=len(GRAPH.get(nid,{}).get('outgoing',[])); w=[float(x) for x in lst(raw.get('steer_power'))]
            if k>=2 and len(w)==k and fl(raw.get('outgoing'),0)>0 and any('type' in e and 'val' in e for e in ents.values()):
                yield sid,nid,raw,ents,k,w
def share(ents,k,f):
    s=[0.0]*k
    for e in ents.values():
        if 'type' in e and 'val' in e:
            l=int(fl(e.get('steer_power'),0)); 
            if l<k: s[l]+=f(e)
    T=sum(s); return [x/T for x in s] if T else None
for label,ids in (('S79+S80',['S79','S80']),('all4',['S79','S80','U01','U02'])):
    c=Counter()
    for sid,nid,raw,ents,k,w in inst(ids):
        c['n']+=1
        for name,f in (('val',lambda e:fl(e['val'])),('eff',eff),('max_pow',lambda e:fl(e.get('max_pow'),0))):
            sh=share(ents,k,f)
            c[name]+= sh is not None and all(abs(a-b)<=0.0011 for a,b in zip(sh,w))
    print(label,dict(c))
# trivial [1,0] cases
c=Counter()
for sid,nid,raw,ents,k,w in inst(['S79','S80']):
    links={int(fl(e.get('steer_power'),0)) for e in ents.values() if 'type' in e and 'val' in e}
    c['single_link' if len(links)==1 else 'multi_link']+=1
    sh=share(ents,k,eff)
    if len(links)>1: c['multi_eff_ok']+= all(abs(a-b)<=0.0011 for a,b in zip(sh,w))
print('trivial vs non-trivial',dict(c))
