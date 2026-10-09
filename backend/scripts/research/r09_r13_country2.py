"""R09 Q4 follow-up: envoy action codes vs entries; what `traded` aggregates."""
import sys,re,collections
sys.path.insert(0,'scripts/research')
import common
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
def al(x): return x if isinstance(x,list) else [x]
st=collections.Counter(); ex=[]
cand=collections.defaultdict(lambda:[0,0])
shipfail=collections.Counter()
for e in common.entries():
    C=common.block(e,'countries'); ns=common.nodes(e)
    agg=collections.defaultdict(lambda:collections.Counter())
    for n in ns:
        for t,v in n.items():
            if not(TAG.match(t) and isinstance(v,dict)): continue
            a=agg[t]
            a['traders']+=bool(v.get('has_trader')); a['steer']+= 'type' in v; a['collect_trader']+=('total' in v and bool(v.get('has_trader')))
            a['capital']+=bool(v.get('has_capital'))
            a['money']+=v.get('money',0.0); a['share_total']+=v.get('total',0.0) if 'total' in v and isinstance(v.get('total'),float) else 0
            if 'total' in v: a['node_current_collect']+=n.get('current',0.0)
            a['ships']+=v.get('light_ship',0)
            a['val']+=v.get('val',0.0)
            a['nodes_with_power']+=bool(v.get('val'))
    for t,c in C.items():
        if not isinstance(c,dict) or 'merchants' not in c and not agg[t]['traders']: continue
        env=al(c.get('merchants',{}).get('envoy',[])) if isinstance(c.get('merchants'),dict) else []
        a2=sum(1 for m in env if m.get('action')==2); a1=sum(1 for m in env if m.get('action')==1); a0=sum(1 for m in env if 'action' not in m)
        A=agg[t]
        for nm,val in (('action==2 count == #nodes has_trader',a2==A['traders']),('action==2 count == #nodes has_trader (a1 incl)',a2+a1==A['traders']),('#envoys total >= #has_trader',len(env)>=A['traders'])):
            st[nm+' checks']+=1; st[nm+' FAIL']+= (not val)
        if a2!=A['traders'] and len(ex)<5: ex.append((e['id'],t,'action2',a2,'action1',a1,'noaction',a0,'has_trader nodes',A['traders']))
        if 'traded' in c:
            s=sum(al(c['traded']))
            for nm in ('money','share_total','node_current_collect','val'):
                cand[nm][0]+=1; cand[nm][1]+= abs(s-A[nm])<0.01
        if 'num_ships_protecting_trade' in c and c['num_ships_protecting_trade']!=A['ships']: shipfail[e['id']]+=1
for k in sorted(st): print(k,st[k])
print(ex); print({k:tuple(v) for k,v in cand.items()}); print('ship mismatch by save',dict(shipfail))
