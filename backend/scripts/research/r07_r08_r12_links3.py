import sys, math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_steer1 import *
from collections import Counter
S=Counter(); bad=[]; sel_variants=Counter()
for e,ns in all_saves():
    by={n['id']:n for n in ns}
    for n in ns:
        out=f(n['raw'].get('outgoing'))
        if not n['links'] or out is None or len(n['w'])!=len(n['links']): continue
        k=len(n['links'])
        for i,t in enumerate(n['links']):
            inc=[(v,a) for s,v,a in by[t]['incoming'] if s==n['id']]
            if len(inc)!=1: continue
            v,a=inc[0]
            members=[x for x in n['ents'].values() if 'type' in x and link_of(x)==i]
            sa=sum(f(x.get('add'),0) for x in members)
            lo=out*n['w'][i]*sa-0.0021-out*n['w'][i]*0.001*len(members)
            hi=out*(n['w'][i]+0.001)*sa+0.0011+out*n['w'][i]*0.001*len(members)
            ok=lo<=a<=hi
            S['ok' if ok else 'bad']+=1
            if not ok: bad.append((e['id'],n['id'],i,out,n['w'][i],sa,a,len(members)))
            S['add>0']+= a>0
            S['steerers_with_add==0_but_link_add>0']+= (sa==0 and a>0)
print(S); print(bad[:10])
