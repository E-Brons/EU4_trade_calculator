"""R01/R10: embargo rows in the Venice series (AI embargoes GEN<->LAN, FRA->ENG): observed reduction vs the formula 0.5*sum(own_e)/(sum(own)+5*NH)."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_load as V, venice_c_lib as L

def own(e): return (e.get('max_pow',0)-e.get('prev',0)) if 'max_pow' in e else 0.0

def analyse(idx, show=True):
    p=V.files()[idx]; ns=V.nodes(p); cs=V.load(p,'countries')
    emb={t:c['trade_embargoed_by'] for t,c in cs.items() if isinstance(c,dict) and c.get('trade_embargoed_by')}
    res=[]
    for x,by in emb.items():
        by=L.as_list(by)
        rows=[]
        for n in ns:
            e=n.get(x)
            if not isinstance(e,dict) or 'max_demand' not in e: continue
            ents=[v for k,v in n.items() if isinstance(v,dict) and L.TAGLIKE(k)]
            NH=sum(1 for v in ents if v.get('has_capital'))
            tot=sum(own(v) for v in ents)+5*NH
            emb_own=sum(own(n[b]) for b in by if isinstance(n.get(b),dict))
            rows.append((n['definitions'],e['max_demand'],emb_own,tot,bool(e.get('has_capital'))))
        cap=max(set(r[1] for r in rows if r[2]<=0 and not r[4]) or {0}, key=lambda v: sum(1 for r in rows if r[1]==v and r[2]<=0))
        for nm,md,eo,tot,hc in rows:
            if eo>0:
                obs=1-md/cap; pred=0.5*eo/tot if tot else 0
                res.append((x,by,nm,md,cap,round(obs*100,2),round(pred*100,2),hc))
    return res

if __name__=='__main__':
    for idx in (7,11,17,19,24,25,26,29):
        r=analyse(idx)
        ok=sum(1 for *_,obs,pred,hc in r if abs(obs-pred)<=1.0 and not hc)
        print(f"U{7+idx:02d} rows with embargoer power: {len(r)}; within 1pp of prediction: {ok}")
        for row in r[:6]: print('   ',row)

def summary():
    print('save: embargo pairs | rows with embargoer power (excl. home node) | reduced (obs>0.3pp) | within 1pp of formula | obs~0 while pred>1pp')
    for idx,p in enumerate(V.files()):
        r=[x for x in analyse(idx) if not x[7]]
        red=sum(1 for x in r if x[5]>0.3)
        ok=sum(1 for x in r if abs(x[5]-x[6])<=1.0)
        zero=sum(1 for x in r if x[5]<=0.3 and x[6]>1.0)
        cs=V.load(p,'countries')
        pairs=sorted((t,tuple(L.as_list(c['trade_embargoed_by']))) for t,c in cs.items() if isinstance(c,dict) and c.get('trade_embargoed_by'))
        print(f"U{7+idx:02d} {p.stem[6:]}: {pairs} | {len(r)} | {red} | {ok} | {zero}")
