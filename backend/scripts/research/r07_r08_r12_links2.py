import sys, math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_steer1 import *
from collections import Counter
S=Counter(); bad=[]
for e,ns in all_saves():
    by={n['id']:n for n in ns}
    for n in ns:
        out=f(n['raw'].get('outgoing'))
        if not n['links'] or out is None or len(n['w'])!=len(n['links']): continue
        k=len(n['links']); incs=[]
        for t in n['links']:
            inc=[(v,a) for s,v,a in by[t]['incoming'] if s==n['id']]
            incs.append(inc[0] if len(inc)==1 else None)
        if any(x is None for x in incs): S['skip']+=1; continue
        S['nodes']+=1
        okall=True
        for i,(v,a) in enumerate(incs):
            lo=out*n['w'][i]-0.002; hi=out*(n['w'][i]+0.001)+0.002   # weight truncated to 3 dp; value truncated to 3 dp
            ok = lo<= (v-a) <= hi
            S['link_ok' if ok else 'link_bad']+=1
            okall&=ok
            if not ok: bad.append((e['id'],n['id'],i,out,n['w'][i],v,a))
        sw=sum(n['w']); 
        S['sumw==1 (>=.998)']+= sw>=0.998 and sw<=1.0005
        S['sumw_hist_%.3f'%sw]+=1
        tot=sum(v for v,a in incs); adds=sum(a for v,a in incs)
        S['(sum value - sum add) within out*(1-sumw)+-.003k']+= abs((tot-adds)-out)<= out*max(0,1-sw)+0.003*k+out*0.001*k
        okall and 0
print({k:v for k,v in S.items() if not k.startswith('sumw_hist')})
print(sorted((k,v) for k,v in S.items() if k.startswith('sumw_hist'))[:12])
print(bad[:10], len(bad))
