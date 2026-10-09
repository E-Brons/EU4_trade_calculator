"""Foreign-class max_demand minus the domestic class vs ruler DIP (U07, S01)."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_c_lib as L, venice_load as V, common
from venice_c_dip import ruler
S=L.series()
s01=[e for e in common.entries() if e['id']=='S01'][0]
games=[('S01',L.entries_of(S[0][1]),common.block(s01,'countries')),('U07',L.entries_of(S[1][1]),V.load(V.files()[0],'countries'))]
for lab,tab,cs in games:
    byc=collections.defaultdict(collections.Counter)
    for (n,t),e in tab.items():
        if 'max_demand' in e: byc[t][e['max_demand']]+=1
    rows=[]
    for t,c in byc.items():
        if not isinstance(cs.get(t),dict): continue
        r=ruler(cs[t])
        if not r: continue
        foreign=c.most_common(1)[0][0]
        dom=min(c) if len(c)>1 else None
        rows.append((t,foreign,dom,r['DIP'],len(c)))
    two=[r for r in rows if r[4]==2]
    print(lab,'countries',len(rows),'two-valued',len(two))
    bydip=collections.defaultdict(set)
    for t,f,d,dip,_ in two:
        bydip[dip].add(round(f-d,3))
    print({k:sorted(v) for k,v in sorted(bydip.items())})

print('=== S01 vs U07 per country: delta foreign class vs 0.005 * delta DIP')
import math
a_tab,a_cs=games[0][1],games[0][2]; b_tab,b_cs=games[1][1],games[1][2]
def classes(tab):
    byc=collections.defaultdict(collections.Counter)
    for (n,t),e in tab.items():
        if 'max_demand' in e: byc[t][e['max_demand']]+=1
    return byc
A,B=classes(a_tab),classes(b_tab)
res=collections.Counter(); exceptions=[]
for t in A:
    if t not in B or not isinstance(a_cs.get(t),dict) or not isinstance(b_cs.get(t),dict): continue
    ra,rb=ruler(a_cs[t]),ruler(b_cs[t])
    if not ra or not rb: res['no ruler']+=1; continue
    fa=A[t].most_common(1)[0][0]; fb=B[t].most_common(1)[0][0]
    da=min(A[t]); db=min(B[t])
    ddip=rb['DIP']-ra['DIP']
    two=len(A[t])==2 and len(B[t])==2
    key=('two-class' if two else 'one-class', 'dip changed' if ddip else 'dip same')
    ok=abs(round(fb-fa,3)-0.005*ddip)<1e-9 and (da==db or not two)
    res[key+(ok,)]+=1
    if not ok and two: exceptions.append((t,fa,fb,da,db,ddip))
for k,v in sorted(res.items(),key=str): print(k,v)
print(exceptions[:10])
