"""R09 Q4: country field transfer_home_bonus vs number of the country's merchants steering into its home (has_capital) node."""
import sys,re,collections
sys.path.insert(0,'scripts/research')
import common
from app.parsing.tradenodes import load_trade_graph
g=load_trade_graph(); TAG=re.compile(r'^[A-Z0-9]{2,4}$')
posS=set(); st=collections.Counter(); ex=[]; hist=collections.Counter()
for e in common.entries():
    C=common.block(e,'countries'); ns=common.nodes(e)
    cap={}; into=collections.Counter(); steer_total=collections.Counter(); away_collect=collections.Counter()
    for n in ns:
        nid=n['definitions']
        for t,v in n.items():
            if TAG.match(t) and isinstance(v,dict) and v.get('has_capital'): cap[t]=nid
    for n in ns:
        nid=n['definitions']; outs=g.outgoing(nid) if nid in g else ()
        for t,v in n.items():
            if TAG.match(t) and isinstance(v,dict) and 'type' in v and v.get('has_trader'):
                li=int(v.get('steer_power',0)); tgt=outs[li] if li<len(outs) else None
                steer_total[t]+=1
                if tgt is not None and cap.get(t)==tgt: into[t]+=1
            if TAG.match(t) and isinstance(v,dict) and 'total' in v and v.get('has_trader') and cap.get(t)!=nid and t in cap: away_collect[t]+=1
    for t,c in C.items():
        if isinstance(c,dict) and 'transfer_home_bonus' in c and t in cap:
            b=round(c['transfer_home_bonus'],3); hist[b]+=1
            if b>0: posS.add(e['id'])
            pred=round(min(0.1*into[t],1.0),3)
            st['countries']+=1
            if b>0:
                st['bonus>0']+=1; st['bonus>0 and equals pred']+= abs(b-pred)<0.0015; st['bonus>0 and away_collect==0']+= away_collect[t]==0
            if pred>0 and b==0:
                st['pred>0 but bonus==0']+=1; st['  of which away_collect>0']+= away_collect[t]>0
            if pred>0 and b>0: st['pred>0 and bonus>0']+=1
            if abs(b-pred)<0.0015: st['bonus == 0.1 * #steering merchants whose target is the home node (cap 1.0)']+=1
            elif len(ex)<6: ex.append((e['id'],t,b,into[t],steer_total[t],away_collect[t]))
print(dict(st)); print(ex); print('saves with bonus>0',sorted({k for k in posS})); print(hist.most_common(12))
