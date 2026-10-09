"""Second pass B: S01 vs U07 (regex readers): 34 countries differ; delta(foreign class) == 0.005 * delta(ruler DIP)."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_c_raw as R
ta,tb=R.read('S01_VEN_1444.11.11.eu4'),R.read('Venice1444_11_11.eu4')
ea,_=R.trade_entries(ta); eb,_=R.trade_entries(tb)
def classes(e):
    c=collections.defaultdict(collections.Counter)
    for (n,t),v in e.items():
        if 'max_demand' in v: c[t][v['max_demand']]+=1
    return c
A,B=classes(ea),classes(eb)
differ=sorted(t for t in A if t in B and (A[t]!=B[t]))
print('countries with any max_demand difference between S01 and U07:',len(differ))
nodes_changed=sum(1 for k in ea if k in eb and ea[k].get('max_demand')!=eb[k].get('max_demand'))
print('node entries with different max_demand:',nodes_changed)
res=collections.Counter(); exc=[]
for t in differ:
    sa,sb=R.country_segment(ta,t),R.country_segment(tb,t)
    da,db=R.ruler_dip(sa),R.ruler_dip(sb)
    fa=A[t].most_common(1)[0][0]; fb=B[t].most_common(1)[0][0]
    ok = da is not None and db is not None and abs((fb-fa)-0.005*(db-da))<1e-9
    res[ok]+=1
    if not ok: exc.append((t,fa,fb,da,db))
print('of the differing countries, foreign-class delta == 0.005*delta DIP:',dict(res), exc[:5])
# countries with DIP change but no md change (independent count over all countries present in both)
import re
tags=sorted({t for (_,t) in ea if t in A and t in B})
chg=0; same=0
for t in tags:
    if t=='PIR': continue
    sa,sb=R.country_segment(ta,t),R.country_segment(tb,t)
    da,db=R.ruler_dip(sa),R.ruler_dip(sb)
    if da is None or db is None or da==db: continue
    if A[t]==B[t]: same+=1
    else: chg+=1
print('countries with changed ruler DIP: scalar changed',chg,'scalar unchanged',same)
