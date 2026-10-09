"""Is the tick change of the foreign-class max_demand scalar proportional to the change of `corruption`?"""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_c_lib as L, venice_load as V
from venice_c_tick_scalar import mode_md, F, num
for a,b in [(2,3),(6,7),(12,13),(17,18),(19,20),(20,21),(21,22),(22,23)]:
    ma,mb=mode_md(V.nodes(F[a])),mode_md(V.nodes(F[b]))
    ca,cb=V.load(F[a],'countries'),V.load(F[b],'countries')
    pts=[]
    for t in ma:
        if t in mb and isinstance(ca.get(t),dict) and isinstance(cb.get(t),dict):
            x=ca[t].get('corruption'); y=cb[t].get('corruption')
            if num(x) and num(y): pts.append((round(y-x,3),round(mb[t]-ma[t],3),t))
    nz=[p for p in pts if p[0]!=0 or p[1]!=0]
    ratios=collections.Counter(round(p[1]/p[0],3) for p in nz if p[0]!=0)
    print(f"U{7+a:02d}->U{7+b:02d}: countries with corruption {len(pts)}, with any change {len(nz)}; dmd/dcorruption {ratios.most_common(4)}; md changed with corruption unchanged: {sum(1 for p in nz if p[0]==0 and p[1]!=0)}; corruption changed, md unchanged: {sum(1 for p in nz if p[0]!=0 and p[1]==0)}")
