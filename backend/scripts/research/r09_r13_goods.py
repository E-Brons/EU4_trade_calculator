"""R13 Q1 / R09 Q2: map trade_goods_size index -> goods name by fitting against provinces' trade_goods x base_production,
then fit local_value = sum(size_g * price_g). Reads the cached pickles directly (needs numpy; run with system python3)."""
import pickle, collections, sys
import numpy as np
C='/tmp/eu4research/cache/'
def al(x): return x if isinstance(x,list) else [x]
def load(k,i): return pickle.load(open(f'{C}{k}_{i}.pkl','rb'))
SAVES=sys.argv[1:] or ['S01','S14','S42','S36','S60']
rows=[]; names=set()
for sid in SAVES:
    prov=load('provinces',sid); tr=load('trade',sid)
    per=collections.defaultdict(lambda:collections.defaultdict(float))
    for p in prov.values():
        if isinstance(p,dict) and 'trade' in p and 'trade_goods' in p and p.get('owner'):
            per[p['trade']][p['trade_goods']]+=p.get('base_production',0.0); names.add(p['trade_goods'])
    for n in al(tr['node']):
        if isinstance(n,dict) and 'trade_goods_size' in n:
            rows.append((sid,n['definitions'],np.array(al(n['trade_goods_size'])),per[n['definitions']],n.get('local_value')))
names=sorted(names); L=len(rows[0][2])
B=np.array([r[2] for r in rows]); A=np.array([[r[3].get(g,0.0) for g in names] for r in rows])
print('goods names in provinces',len(names),'array length',L,set(len(r[2]) for r in rows))
mapping={}
for i in range(L):
    cs=[]
    for j in range(len(names)):
        if B[:,i].std()>0 and A[:,j].std()>0: cs.append((np.corrcoef(B[:,i],A[:,j])[0,1],names[j]))
    cs.sort(reverse=True)
    if not cs: print(i,'all zero'); continue
    j=names.index(cs[0][1]); m=A[:,j]>0
    mapping[i]=cs[0][1]
    print(i,cs[0][1],round(cs[0][0],4),'second',cs[1][1] if len(cs)>1 else None,round(cs[1][0],3) if len(cs)>1 else None,'median size/base_production',round(float(np.median(B[m,i]/A[m,j])),4))

# --- local_value ~ sum(size_g * price_g) ; fit prices (least squares) per save, report residuals
print('\nlocal_value fit (per save): lstsq prices for goods with any size')
for sid in SAVES:
    rs=[r for r in rows if r[0]==sid and r[4] is not None]
    X=np.array([r[2] for r in rs]); y=np.array([r[4] for r in rs])
    used=[i for i in range(L) if X[:,i].std()>0 or X[:,i].any()]
    coef,res,rk,sv=np.linalg.lstsq(X[:,used],y,rcond=None)
    pred=X[:,used]@coef
    print(sid,'nodes',len(rs),'max abs resid',round(float(np.abs(pred-y).max()),3),'rank',rk,'of',len(used))
    print('  prices',{mapping.get(i,i):round(float(c),3) for i,c in zip(used,coef)})
