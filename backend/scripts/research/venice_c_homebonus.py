"""R01/R09: country field transfer_home_bonus vs the number of steering merchants (entries with `type`), all countries, all saves."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_load as V, venice_c_lib as L
res=collections.Counter(); bad=[]
for i,p in enumerate(V.files()):
    cs=V.load(p,'countries'); ns=V.nodes(p)
    steer=collections.Counter(); 
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and e.get('has_trader') and 'type' in e: steer[k]+=1
    for t,c in cs.items():
        if not isinstance(c,dict) or 'transfer_home_bonus' not in c: continue
        ok=abs(c['transfer_home_bonus']-0.1*steer[t])<1e-6
        res[(i>0,ok)]+=1
        if not ok and i>0 and len(bad)<8: bad.append((p.stem[6:],t,c['transfer_home_bonus'],steer[t]))
print(res); print(bad)

print('--- misses by save; is the field equal to 0.1 x steerers of the previous / next save?')
F=V.files()
cnt=[]
for p in F:
    cs=V.load(p,'countries'); ns=V.nodes(p)
    st=collections.Counter()
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and e.get('has_trader') and 'type' in e: st[k]+=1
    cnt.append((cs,st))
miss=collections.Counter(); kinds=collections.Counter()
for i in range(1,len(F)):
    cs,st=cnt[i]
    for t,c in cs.items():
        if not isinstance(c,dict) or 'transfer_home_bonus' not in c: continue
        if abs(c['transfer_home_bonus']-0.1*st[t])>1e-6:
            miss[F[i].stem[6:]]+=1
            prev_ok=abs(c['transfer_home_bonus']-0.1*cnt[i-1][1][t])<1e-6
            next_ok=i+1<len(F) and abs(c['transfer_home_bonus']-0.1*cnt[i+1][1][t])<1e-6
            kinds[('equals previous save count' if prev_ok else '', 'equals next save count' if next_ok else '')]+=1
print(dict(miss)); print(kinds)
