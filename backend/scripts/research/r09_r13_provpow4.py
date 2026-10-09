"""R13 Q3 final: tolerance 0.0005 per summed province (display rounding), REB (rebel controller) accounted; p_pow and highest_power."""
import sys,re,collections
sys.path.insert(0,'scripts/research')
import common
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
st=collections.Counter(); fails=[]; ppfails=[]; hpfails=[]
for e in common.entries():
    prov=common.block(e,'provinces'); ns=common.nodes(e)
    sums=collections.defaultdict(float); k=collections.Counter(); mx=collections.defaultdict(float); rebs=collections.defaultdict(float)
    for pid,p in prov.items():
        if not isinstance(p,dict) or 'trade' not in p or p.get('trade_power') is None: continue
        c=p.get('controller')
        if c: sums[(p['trade'],c)]+=p['trade_power']; k[(p['trade'],c)]+=1
        mx[p['trade']]=max(mx[p['trade']],p['trade_power'])
    for n in ns:
        nid=n['definitions']
        es={t:v for t,v in n.items() if TAG.match(t) and isinstance(v,dict)}
        allsum=0.0; allk=0
        for t in {tt for (nn,tt) in sums if nn==nid}|set(es):
            s=sums.get((nid,t),0.0); allsum+=s; allk+=k.get((nid,t),0)
            if t=='REB' and t not in es: st['REB-controlled (node,controller) groups with trade_power>0']+= s>0; continue
            pp=es.get(t,{}).get('province_power',0.0)
            if pp>0 or s>0: st['pairs']+=1
            if abs(pp-s)>0.0005*max(1,k.get((nid,t),0))+0.0005:
                st['pair fail']+=1; fails.append((e['id'],nid,t,pp,round(s,3),round(pp-s,3)))
        if 'p_pow' in n:
            st['p_pow nodes']+=1
            if abs(n['p_pow']-allsum)>0.0005*max(1,allk)+0.0005: ppfails.append((e['id'],nid,n['p_pow'],round(allsum,3)))
            if 'highest_power' in n:
                st['highest_power nodes']+=1
                if abs(n['highest_power']-mx.get(nid,0))>0.0015: hpfails.append((e['id'],nid,n['highest_power'],round(mx.get(nid,0),3)))
print(dict(st))
print('pair fails by save',collections.Counter(f[0] for f in fails).most_common(12))
print('pair fail diff hist',collections.Counter(abs(f[5])>=0.5 for f in fails))
print('big pair fails',[f for f in fails if abs(f[5])>=0.5][:25])
import collections as _c
print("p_pow fails",len(ppfails),"in played saves",sum(1 for f in ppfails if f[0] in ("S79","S80","U01","U02")),"diff hist outside played",_c.Counter(round(f[2]-f[3],2) for f in ppfails if f[0] not in ("S79","S80","U01","U02")).most_common(8)); print("p_pow fail saves outside played",_c.Counter(f[0] for f in ppfails if f[0] not in ("S79","S80","U01","U02")).most_common(30)); print("hp fails",len(hpfails),"in played",sum(1 for f in hpfails if f[0] in ("S79","S80","U01","U02")))
