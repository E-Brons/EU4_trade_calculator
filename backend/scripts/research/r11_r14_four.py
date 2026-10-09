"""R11 Q4: what separates the 4 on_my_way=False fleets that are not counted from the 225 counted."""
import sys; sys.path.insert(0,'scripts/research')
exec(open('scripts/research/r11_r14_fleetflags.py').read().split("unique=0")[0])
from statistics import median
def feat(f): return dict(cyc=f['cyc'],tgt=f['tgt'],rl=f['route_len'],mp=f['mp'],n=f['n'],keys=tuple(f['keys']))
nps=Counter(); bad=[]
C=[];U=[]
for sid,key,en,lst,sols in rows:
    if len(sols)!=1: continue
    for i,f in enumerate(lst):
        if f['on_my_way'] is None: continue
        (C if i in sols[0] else U).append((sid,key,f))
print('counted fleets: cyc>=? min',min(f['cyc'] for *_,f in C),'tgt values',Counter(f['tgt'] for *_,f in C).most_common(6))
print('with n==1 and has_path counted',sum(1 for *_,f in C if f['n']==1 and f['has_path']),'of',sum(1 for *_,f in C if f['n']==1))
for sid,key,f in U: print('UNCOUNTED',sid,key,f['fleet'],'cyc',f['cyc'],'tgt',f['tgt'],'route_len',f['route_len'],'mp',f['mp'],'extra keys',f['keys'])
print('counted with tgt>=cyc fraction', sum(1 for *_,f in C if f['tgt']>=f['cyc']),len(C))
print('uncounted tgt>=cyc', [(f['cyc'],f['tgt']) for *_,f in U])
# fleets whose node already has another counted fleet
