"""R01: which country field changes together with the foreign-class max_demand scalar at a monthly tick? (correlation of deltas over all countries, per tick)"""
import sys, math, statistics, collections
sys.path.insert(0,'scripts/research')
import venice_c_lib as L, venice_load as V
F=V.files()
def mode_md(ns):
    c=collections.defaultdict(collections.Counter)
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and 'max_demand' in e: c[k][e['max_demand']]+=1
    return {k:v.most_common(1)[0][0] for k,v in c.items()}
def num(x): return isinstance(x,(int,float)) and not isinstance(x,bool)
ticks=[(2,3),(6,7),(12,13),(17,18),(19,20),(20,21),(21,22),(22,23)]
for a,b in ticks:
    ma,mb=mode_md(V.nodes(F[a])),mode_md(V.nodes(F[b]))
    ca,cb=V.load(F[a],'countries'),V.load(F[b],'countries')
    rows=[(t,mb[t]-ma[t]) for t in ma if t in mb and isinstance(ca.get(t),dict) and isinstance(cb.get(t),dict)]
    chg=[r for r in rows if abs(r[1])>1e-9]
    fields=set()
    for t,_ in rows:
        for k,v in ca[t].items():
            if num(v) and num(cb[t].get(k)): fields.add(k)
    res=[]
    for k in fields:
        xs=[cb[t][k]-ca[t][k] for t,_ in rows if num(ca[t].get(k)) and num(cb[t].get(k))]
        ys=[d for t,d in rows if num(ca[t].get(k)) and num(cb[t].get(k))]
        if len(xs)>30 and statistics.pstdev(xs)>0 and statistics.pstdev(ys)>0:
            mx,my=statistics.mean(xs),statistics.mean(ys)
            c=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/len(xs)/(statistics.pstdev(xs)*statistics.pstdev(ys))
            res.append((round(abs(c),3),k,len(xs)))
    res.sort(reverse=True)
    print(f"U{7+a:02d}->U{7+b:02d}: countries {len(rows)}, scalar changed {len(chg)}; top correlated fields {res[:5]}")
