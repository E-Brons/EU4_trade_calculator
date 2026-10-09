import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_load import *
SAVES=('S79','S80','U01','U02')
def feats(x):
    val=f(x.get('val'),0); tout=f(x.get('t_out'),0); tin=f(x.get('t_in'),0)
    return dict(val=val, eff=val-tout+tin, mp=f(x.get('max_pow'),0), pp=f(x.get('province_power'),0), prev=f(x.get('prev'),0))
def link_of(x): return int(f(x.get('steer_power'),0))
def shares(n, sel, q):
    k=len(n['links']); s=[0.0]*k
    for t,x in n['ents'].items():
        if 'val' in x and sel(x):
            l=link_of(x)
            if l<k: s[l]+=feats(x)[q]
    tot=sum(s)
    return [v/tot if tot else None for v in s] if tot else None
SEL={'type':lambda x:'type' in x,
     'type|sp':lambda x:'type' in x or 'steer_power' in x,
     'noncollect':lambda x:'total' not in x,
     'noncollect_merch':lambda x:'total' not in x and x.get('has_trader'),
     'all':lambda x:True}
if __name__=='__main__':
    res={}
    for e,ns in all_saves():
        if e['id'] not in SAVES: continue
        for n in ns:
            if len(n['links'])<2 or not n['w'] or not n['raw'].get('outgoing'): continue
            for sn,sel in SEL.items():
                for q in ('val','eff','mp','pp'):
                    sh=shares(n,sel,q)
                    ok = sh is not None and all(abs(a-b)<=0.0011 for a,b in zip(sh,n['w']))
                    c=res.setdefault((sn,q),[0,0]); c[0]+=ok; c[1]+=1
    for k,v in sorted(res.items(), key=lambda kv:-kv[1][0]): print(k,v)
