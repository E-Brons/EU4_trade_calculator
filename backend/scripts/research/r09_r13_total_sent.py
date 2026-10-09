"""R09 Q2: node `total` gap vs REB-controlled provinces; `already_sent`."""
import sys,re,collections
sys.path.insert(0,'scripts/research')
import common
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
st=collections.Counter(); ex=collections.defaultdict(list); rel=collections.defaultdict(lambda:[0,0])
sample=[]
for e in common.entries():
    prov=common.block(e,'provinces'); reb=collections.defaultdict(float); 
    for p in prov.values():
        if isinstance(p,dict) and p.get('controller')=='REB' and 'trade' in p and p.get('trade_power') is not None: reb[p['trade']]+=p['trade_power']
    for n in common.nodes(e):
        es={t:v for t,v in n.items() if TAG.match(t) and isinstance(v,dict)}
        if 'total' in n:
            gap=n['total']-sum(v.get('val',0) for v in es.values())
            r=reb.get(n['definitions'],0.0)
            st['nodes']+=1
            if abs(gap)>0.01:
                st['nodes with total-sum(val) gap>0.01']+=1
                if abs(gap-r)<=0.01+0.0005*5: st['  gap == REB-controlled trade_power']+=1
                else:
                    st['  gap != REB']+=1
                    if len(ex['gap'])<8: ex['gap'].append((e['id'],n['definitions'],round(gap,3),round(r,3)))
            elif r>0.01: st['REB power >0 but no gap']+=1
        for t,v in es.items():
            if 'already_sent' in v:
                st['already_sent entries']+=1
                a=v['already_sent']
                for nm,val in (('val',v.get('val')),('t_out',v.get('t_out')),('prev',v.get('prev')),('max_pow',v.get('max_pow')),('eff',v.get('val',0)-v.get('t_out',0)+v.get('t_in',0)),('money',v.get('money')),('province_power',v.get('province_power')),('node.outgoing',n.get('outgoing')),('node.current',n.get('current')),('node.total',n.get('total'))):
                    if val is not None:
                        rel[nm][0]+=1; rel[nm][1]+= abs(a-val)<0.0015
                if len(sample)<6 and e['id']=='S14': sample.append((n['definitions'],t,{k:v[k] for k in v if k in('already_sent','val','max_pow','prev','province_power','t_out','t_in','has_trader','type','total','potential')}, n.get('total')))
print(dict(st)); print(dict(ex)); print({k:tuple(v) for k,v in rel.items()}); print(sample)
