"""R10: is total - sum(val) == trade_power of provinces not credited to their owner (province controller is REB/none)?"""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
res=collections.Counter(); bad=[]; per_owner=collections.Counter(); po_bad=[]
kinds=collections.Counter(); resid=[]
for e in common.entries():
    ps=common.block(e,'provinces')
    byn=collections.defaultdict(list)
    for k,p in ps.items():
        if isinstance(p,dict) and 'trade' in p:
            byn[p['trade']].append(p)
    for n in common.nodes(e):
        if n.get('total') is None: continue
        nid=n['definitions']
        ents={k:v for k,v in n.items() if TAG.match(k) and isinstance(v,dict)}
        sv=sum(v.get('val',0) for v in ents.values())
        gap=n['total']-sv
        own_ok=collections.defaultdict(float); unc=0.0; tp_all=0.0
        for p in byn.get(nid,[]):
            tp=float(p.get('trade_power',0) or 0); tp_all+=tp
            o=p.get('owner'); c=p.get('controller')
            if c is not None and c!='REB' and tp!=0: own_ok[c]+=tp
            else:
                unc+=tp
                kinds[('owned' if o else 'unowned', 'ctrl=none' if c is None else ('ctrl=REB' if c=='REB' else 'ctrl=other'))]+=1
        ok=abs(gap-unc)<0.0035
        res[ok]+=1
        resid.append((e['id'],nid,round(gap-unc,3),round(gap,3),round(unc,3)))
        if not ok and len(bad)<15: bad.append((e['id'],nid,round(gap,3),round(unc,3)))
        # per-owner check
        for t,v in ents.items():
            lp=v.get('province_power',0.0)
            good=abs(lp-own_ok.get(t,0.0))<0.0035
            per_owner[good]+=1
            if not good and len(po_bad)<10: po_bad.append((e['id'],nid,t,lp,round(own_ok.get(t,0.0),3)))
print('nodes: gap == tp of provinces not credited to owner :',dict(res))
print('entry province_power == sum trade_power of provinces whose controller is the tag:',dict(per_owner))
print('uncredited province kinds',dict(kinds))
print(bad); print(po_bad)

r=[x for x in resid if abs(x[2])>0.0035]
print('residual nodes',len(r),'positive',sum(x[2]>0 for x in r),'negative',sum(x[2]<0 for x in r))
print('residual by save',sorted(collections.Counter(x[0] for x in r).items(), key=lambda a:-a[1])[:12])
print('residual size: min/median/max', min(abs(x[2]) for x in r), sorted(abs(x[2]) for x in r)[len(r)//2], max(abs(x[2]) for x in r))
print('largest', sorted(r,key=lambda x:-abs(x[2]))[:6])
print('negative', [x for x in r if x[2]<0][:6])
print('residual nodes where unc==0:',sum(1 for x in r if abs(x[4])<0.0035))
tot=sum(1 for x in resid if abs(x[3])>0.0035); print('nodes with gap>0.0035', tot, 'of which fully explained by REB/none-controlled provinces', sum(1 for x in resid if abs(x[3])>0.0035 and abs(x[2])<=0.0035))
print('--- residual grouped by (save, value)')
g=collections.defaultdict(list)
for x in r: g[(x[0],round(x[2],3))].append(x[1])
for (s,v),nl in sorted(g.items(), key=lambda a:(int(a[0][0][1:]) if a[0][0][0]=='S' else 99, a[0][1])):
    if s in('S70','U01','S80'): continue
    print(s,v,nl)
