"""Natural experiment: S01 vs U07 (same scenario, two fresh games). Which country field changes with the per-country max_demand ratio?"""
import sys, math, collections, statistics
sys.path.insert(0,'scripts/research')
import venice_c_lib as L, venice_load as V, venice_diff as D, common

S=L.series()
t01=L.entries_of(S[0][1]); t07=L.entries_of(S[1][1])
# per country: ratio of max_demand per class value; use the max over nodes (= cap-class?) and min
md1=collections.defaultdict(set); md7=collections.defaultdict(set)
for (n,t),e in t01.items():
    if 'max_demand' in e: md1[t].add(e['max_demand'])
for (n,t),e in t07.items():
    if 'max_demand' in e: md7[t].add(e['max_demand'])
s01=[e for e in common.entries() if e['id']=='S01'][0]
cs=common.block(s01,'countries'); cu=V.load(V.files()[0],'countries')
rows=[]
for t in md1:
    if t in md7 and t in cs and t in cu and isinstance(cs[t],dict) and isinstance(cu[t],dict):
        r=min(md7[t])/min(md1[t])
        rows.append((t,r,cs[t],cu[t]))
print('countries',len(rows),'ratio != 1:',sum(1 for r in rows if abs(r[1]-1)>1e-9))
def num(x): return isinstance(x,(int,float)) and not isinstance(x,bool)
# scalar numeric fields at depth 1
fields=set()
for t,r,a,b in rows:
    for k in a:
        if num(a[k]) and num(b.get(k)): fields.add(k)
res=[]
for k in sorted(fields):
    xs=[];ys=[]
    for t,r,a,b in rows:
        if num(a.get(k)) and num(b.get(k)):
            xs.append(b[k]-a[k]); ys.append(math.log(r))
    if len(xs)>30 and statistics.pstdev(xs)>0 and statistics.pstdev(ys)>0:
        mx,my=statistics.mean(xs),statistics.mean(ys)
        c=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/len(xs)/(statistics.pstdev(xs)*statistics.pstdev(ys))
        res.append((abs(c),k,c,len(xs)))
res.sort(reverse=True)
for r in res[:15]: print(r)
