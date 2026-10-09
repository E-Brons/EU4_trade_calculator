"""R11 Q3/Q6: ship_power / (sum of base trade_power of counted light ships) per country and node; constancy per country; relation to country fields."""
import sys,pickle; sys.path.insert(0,'scripts/research')
exec(open('scripts/research/r11_r14_fleetflags.py').read().split("unique=0")[0])
from collections import defaultdict
per=defaultdict(list)   # (sid,tag)->[(node, ratio, n, sp)]
for sid,key,en,lst,sols in rows:
    if en is None or len(sols)!=1: continue
    base=sum(lst[i]['base'] for i in sols[0]); n=sum(lst[i]['n'] for i in sols[0])
    assert n==en[0]
    per[(sid,key[0])].append((key[1],round(en[1]/base,4),n,en[1]))
incons=0
for k,v in sorted(per.items()):
    rs={r for _,r,_,_ in v}
    if len(rs)>1: incons+=1; print('INCONSISTENT',k,v)
print('country-saves',len(per),'with a single ratio across all its nodes',len(per)-incons)
print('ratio histogram (country-saves):',Counter(round(next(iter({r for _,r,_,_ in v})),3) for v in per.values() if len({r for _,r,_,_ in v})==1))
by={}
for (sid,t),v in per.items(): by.setdefault(t,{})[sid]=sorted({r for _,r,_,_ in v})
diff=[(t,d) for t,d in by.items() if len(d)>1 and d.get('S79')!=d.get('S80')]
print('tags in both S79 and S80 with different ratio:',diff)
pickle.dump({k:v for k,v in per.items()},open('/tmp/eu4research/cache/r11_ratio.pkl','wb'))
print('per-ship max', max(en[1]/en[0] for sid,key,en,lst,sols in rows if en))
print('per-ship min', min(en[1]/en[0] for sid,key,en,lst,sols in rows if en))
