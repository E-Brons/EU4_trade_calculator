"""How each (node,tag) max_demand evolves across U07..U30: which consecutive pairs change, how many countries, how big."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_c_lib as L
S=L.series()[1:]
tabs=[(lab,{k:e['max_demand'] for k,e in L.entries_of(ns).items() if 'max_demand' in e}) for lab,ns in S]
print('entries per save',len(tabs[0][1]))
for (la,a),(lb,b) in zip(tabs,tabs[1:]):
    ch=[(k,a[k],b[k]) for k in a if k in b and a[k]!=b[k]]
    cs=collections.Counter(k[1] for k,_,_ in ch)
    # countries changing in all of their nodes?
    tot=collections.Counter(k[1] for k in a)
    full=sum(1 for t,c in cs.items() if c>=0.9*tot[t])
    mag=sorted(abs(y-x) for _,x,y in ch)
    print(f"{la} -> {lb}: {len(ch)} node-entries in {len(cs)} countries ({full} with >=90% of their nodes); median |d| {mag[len(mag)//2] if mag else 0:.3f} max {mag[-1] if mag else 0:.3f}; entries missing/new {len(set(a)^set(b))}")
