"""Definitive table for the S01-vs-U07 natural experiment (ruler chosen by the country's current monarch id)."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_c_lib as L, venice_load as V, common
from venice_c_xdip import ruler
S=L.series(); t01=L.entries_of(S[0][1]); t07=L.entries_of(S[1][1])
s01=[e for e in common.entries() if e['id']=='S01'][0]
cs=common.block(s01,'countries'); cu=V.load(V.files()[0],'countries')
def cl(tab):
    c=collections.defaultdict(collections.Counter)
    for (n,t),e in tab.items():
        if 'max_demand' in e: c[t][e['max_demand']]+=1
    return c
A,B=cl(t01),cl(t07)
cat=collections.Counter(); nonresp=[]; resp=[]
for t in A:
    if t not in B or not isinstance(cs.get(t),dict) or not isinstance(cu.get(t),dict): continue
    ra,rb=ruler(cs[t]),ruler(cu[t])
    if not ra or not rb: cat['no ruler']+=1; continue
    ddip=rb['DIP']-ra['DIP']
    if ddip==0:
        cat[('dip same','scalar same' if A[t]==B[t] else 'scalar CHANGED')]+=1; continue
    ncls=len(A[t])
    fa=A[t].most_common(1)[0][0]; fb=B[t].most_common(1)[0][0]
    exact=abs((fb-fa)-0.005*ddip)<1e-9
    if A[t]==B[t]:
        cat[('dip changed','scalar same',f'{ncls} value(s)')]+=1
        if ncls>1:
            g=cu[t].get('government'); g=g.get('government') if isinstance(g,dict) else g
            nonresp.append((t,ddip,sorted(A[t]),g))
    else:
        cat[('dip changed','scalar changed','exact 0.005*dDIP' if exact else 'NOT exact')]+=1
        resp.append((t,ddip,round(fb-fa,3)))
for k,v in sorted(cat.items(),key=str): print(k,v)
print('two-class non-responders:',nonresp)
print('responders (tag,dDIP,dForeign):',resp[:40])
