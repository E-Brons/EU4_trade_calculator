"""R13 Q3: node entry province_power vs sum of provinces' trade_power (owner == tag, province.trade == node); node p_pow; highest_power."""
import sys,re,collections
sys.path.insert(0,'scripts/research')
import common
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
st=collections.Counter(); ex=collections.defaultdict(list)
def bad(k,c):
    st[k+' FAIL']+=1
    if len(ex[k])<5: ex[k].append(c)
per_save={}
for e in common.entries():
    prov=common.block(e,'provinces'); ns=common.nodes(e)
    sums=collections.defaultdict(float); mx=collections.defaultdict(float); cnt=collections.Counter()
    unowned=collections.defaultdict(float)
    for pid,p in prov.items():
        if not isinstance(p,dict) or 'trade' not in p: continue
        tp=p.get('trade_power')
        if tp is None: st['province with trade but no trade_power']+=1; continue
        own=p.get('owner')
        if own is None: unowned[p['trade']]+=tp
        else: sums[(p['trade'],own)]+=tp
        mx[p['trade']]=max(mx[p['trade']],tp)
    for n in ns:
        nid=n['definitions']
        es={t:v for t,v in n.items() if TAG.match(t) and isinstance(v,dict)}
        tot_all=0
        for t,v in es.items():
            if 'province_power' in v:
                st['entries with province_power']+=1
                if abs(v['province_power']-sums.get((nid,t),0.0))>0.0015*max(1,1) + 0.0005: bad('province_power==sum(trade_power owner=tag)',(e['id'],nid,t,v['province_power'],round(sums.get((nid,t),0),3)))
            elif sums.get((nid,t),0)>0.0015:
                bad('no province_power but provinces have trade_power',(e['id'],nid,t,round(sums[(nid,t)],3)))
        if 'p_pow' in n:
            allsum=sum(s for (nn,t),s in sums.items() if nn==nid)
            st['nodes with p_pow']+=1
            if abs(n['p_pow']-allsum)>0.01: bad('p_pow==sum(owned provinces trade_power)',(e['id'],nid,n['p_pow'],round(allsum,3),round(unowned.get(nid,0),3)))
            if abs(n['p_pow']-allsum-unowned.get(nid,0))>0.01: bad('p_pow==sum(all provinces incl unowned)',(e['id'],nid,n['p_pow'],round(allsum,3),round(unowned.get(nid,0),3)))
            hp=n.get('highest_power')
            if hp is not None:
                if abs(hp-mx.get(nid,0))>0.0015: bad('highest_power==max single province trade_power',(e['id'],nid,hp,round(mx.get(nid,0),3)))
                st['hp checks']+=1
for k in sorted(st): print(k,st[k])
for k,v in ex.items(): print(k,v)
