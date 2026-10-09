"""R13 Q4: what separates M=1.2 from M=1.45/1.3/1.75 provinces (province keys, buildings, goods)."""
import sys,collections
sys.path.insert(0,'scripts/research')
import common
e=[x for x in common.entries() if x['id']=='S01'][0]
prov=common.block(e,'provinces'); COT={None:0,1:5,2:10,3:25}
by=collections.defaultdict(lambda:collections.Counter()); nm=collections.Counter(); cnt=collections.Counter()
for pid,p in prov.items():
    if not isinstance(p,dict) or 'trade' not in p or p.get('trade_power') is None or not p.get('owner') or p.get('controller')!=p.get('owner'): continue
    dev=p.get('base_tax',0)+p.get('base_production',0)+p.get('base_manpower',0)
    base=0.2*dev+COT.get(p.get('center_of_trade'),0)
    if base<=0: continue
    m=round(p['trade_power']/(base*(1-0.005*p.get('local_autonomy',0))),2)
    if m not in (1.2,1.45,1.3,1.75,1.5,1.2): continue
    cnt[m]+=1
    for k in ('buildings','center_of_trade','trade_goods','capital','is_city','hre','trade_company','latent_trade_goods','estuary'):
        if k in p: by[m][k]+=1
    for b in (p.get('buildings') or {}): by[m]['bld:'+b]+=1
    nm[(m,p['trade'])]+=1
for m in sorted(cnt): print(m,cnt[m],{k:v for k,v in by[m].most_common(8)})
# nodes where M=1.45 dominates
inland=collections.Counter(); 
print('node distribution of M=1.45:',[(n,c) for (m,n),c in nm.most_common(60) if m==1.45][:12])
print('node distribution of M=1.2:',[(n,c) for (m,n),c in nm.most_common(60) if m==1.2][:8])
