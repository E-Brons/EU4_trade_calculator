"""R09 Q3: prev vs downstream province_power; max_pow components. Variants: one hop / all hops, with / without threshold 10."""
import sys,re,collections,math
sys.path.insert(0,'scripts/research')
import common
from app.parsing.tradenodes import load_trade_graph
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
g=load_trade_graph()
def fx(x): return math.trunc(x*1000+1e-9)/1000
st=collections.Counter(); ex=collections.defaultdict(list)
def bad(k,c):
    st[k+' FAIL']+=1
    ex[k].append(c)
for e in common.entries():
    ns=common.nodes(e); by={n['definitions']:n for n in ns}
    for n in ns:
        nid=n['definitions']
        if nid not in g: continue
        es={t:v for t,v in n.items() if TAG.match(t) and isinstance(v,dict)}
        outs=g.outgoing(nid)
        for t,v in es.items():
            if 'max_pow' not in v and 'prev' not in v: continue
            pw=[by[o].get(t,{}).get('province_power',0.0) if o in by else 0.0 for o in outs]
            rec=v.get('prev',0.0)
            variants={'plain sum/5':sum(pw)/5,'thresholded(>=10) sum/5':sum(p for p in pw if p>=10)/5,'thresholded(>10)':sum(p for p in pw if p>10)/5}
            for k,pv in variants.items():
                st['n '+k]+=1
                if abs(fx(pv)-rec)>0.0015: bad(k,(e['id'],nid,t,round(pv,3),rec,[round(x,2) for x in pw]))
            # max_pow decomposition
            if 'max_pow' in v:
                ex_=v['max_pow']-v.get('province_power',0)-v.get('ship_power',0)-v.get('prev',0)
                st['max_pow entries']+=1
                st['extras==0']+= abs(ex_)<0.0015
                st['extras==5 (has_capital, no merchant)']+= abs(ex_-5)<0.0015 and v.get('has_capital',False) and not v.get('has_trader',False)
        # country p_pow 
for k in sorted(st): print(k, st[k])
grp=collections.Counter((c[1],c[2]) for c in ex['thresholded(>=10) sum/5'])
print('threshold failure groups (node,tag): count', grp.most_common(20))
print('saves involved', collections.Counter(c[0] for c in ex['thresholded(>=10) sum/5']).most_common(12))
print([c for c in ex['thresholded(>=10) sum/5'] if c[0] in('S80','S79')][:6])
