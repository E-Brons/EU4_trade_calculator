"""R13 Q3 refinement: which provinces count in an entry's province_power? Variants by owner/controller."""
import sys,re,collections
sys.path.insert(0,'scripts/research')
import common
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
V={'owner':lambda p:p.get('owner'),
   'owner if controller==owner':lambda p:p.get('owner') if p.get('controller')==p.get('owner') else None,
   'controller':lambda p:p.get('controller'),
   'owner if controller==owner else controller':lambda p:p.get('controller') if p.get('controller')!=p.get('owner') else p.get('owner')}
st=collections.Counter(); ex=collections.defaultdict(list)
for e in common.entries():
    prov=common.block(e,'provinces'); ns=common.nodes(e)
    sums={k:collections.defaultdict(float) for k in V}
    for pid,p in prov.items():
        if not isinstance(p,dict) or 'trade' not in p or p.get('trade_power') is None: continue
        for k,f in V.items():
            t=f(p)
            if t: sums[k][(p['trade'],t)]+=p['trade_power']
    for n in ns:
        nid=n['definitions']
        es={t:v for t,v in n.items() if TAG.match(t) and isinstance(v,dict)}
        keys=set(es)|{t for (nn,t) in sums['owner'] if nn==nid}
        for t in keys:
            v=es.get(t,{}); pp=v.get('province_power',0.0)
            for k in V:
                s=sums[k].get((nid,t),0.0)
                st[k+' checks']+=1
                if abs(pp-s)>0.0025:
                    st[k+' FAIL']+=1
                    if len(ex[k])<4: ex[k].append((e['id'],nid,t,pp,round(s,3)))
for k in V: print(k, st[k+' checks'], 'fail', st[k+' FAIL'])
for k,v in ex.items(): print(k,v)
