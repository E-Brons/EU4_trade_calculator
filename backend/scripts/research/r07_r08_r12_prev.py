import sys, math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_steer1 import *
from collections import Counter
def fx(x): return math.trunc(x*1000+1e-9)/1000
kinds={e['id']:e.get('kind','start') for e in common.entries()}
res={}; bad=Counter()
for e,ns in all_saves():
    by={n['id']:n for n in ns}
    c=Counter()
    for n in ns:
        for t,x in n['ents'].items():
            if 'max_pow' not in x: continue
            prev=f(x.get('prev'),0.0)
            s=0.0
            for d in n['links']:
                pp=f(by[d]['ents'].get(t,{}).get('province_power'),0.0) if d in by else 0.0
                if pp>=10: s+=pp
            pred=fx(s/5)
            ok=abs(pred-prev)<=0.0011
            c['ok' if ok else 'bad']+=1
            if not ok and e['id'] in ('S79','S80'): bad[(e['id'],n['id'],t,round(prev,3),round(pred,3))]+=1
    res[e['id']]=c
agg={}
for sid,c in res.items():
    k=kinds[sid]; a=agg.setdefault(k,Counter()); a.update(c)
for k,a in agg.items(): print(k,dict(a), round(a['bad']/(a['ok']+a['bad']),5))
print(list(bad)[:12])
