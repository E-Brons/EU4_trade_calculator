"""max_demand step per ruler DIP point: S01 vs U07 (two fresh games) for the 34 countries whose scalar differs."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_c_lib as L, venice_load as V, common

S=L.series()
t01=L.entries_of(S[0][1]); t07=L.entries_of(S[1][1])
s01=[e for e in common.entries() if e['id']=='S01'][0]
cs=common.block(s01,'countries'); cu=V.load(V.files()[0],'countries')

from venice_c_xdip import ruler

def scal(t,tab):
    v={e['max_demand'] for (n,tt),e in tab.items() if tt==t and 'max_demand' in e}
    return v
ok=0;bad=[];n=0
for t in cs:
    if t not in cu or not isinstance(cs[t],dict) or not isinstance(cu[t],dict): continue
    a,b=ruler(cs[t]),ruler(cu[t])
    v1,v7=scal(t,t01),scal(t,t07)
    if not a or not b or len(v1)!=1 or len(v7)!=1: continue
    n+=1
    dmd=round(list(v7)[0]-list(v1)[0],3); ddip=b['DIP']-a['DIP']
    if abs(dmd-0.005*ddip)<1e-9: ok+=1
    else: bad.append((t,dmd,ddip,a['ADM'],b['ADM'],a['MIL'],b['MIL']))
print('single-valued countries',n,'dmd == 0.005*dDIP:',ok,'bad',len(bad))
print(bad[:15])

print('--- which countries respond to DIP')
rows=[]
for t in cs:
    if t not in cu or not isinstance(cs[t],dict) or not isinstance(cu[t],dict): continue
    a,b=ruler(cs[t]),ruler(cu[t])
    v1,v7=scal(t,t01),scal(t,t07)
    if not a or not b or len(v1)==0 or a['DIP']==b['DIP']: continue
    resp=(min(v7)!=min(v1)) or (max(v7)!=max(v1))
    g=cu[t].get('government'); g=g.get('government') if isinstance(g,dict) else g
    rows.append((resp,t,g,cu[t].get('technology_group'),cu[t].get('num_of_cities'),len(v1),cu[t].get('government_rank'),bool(cu[t].get('subject_of') or cu[t].get('overlord'))))
import collections
c=collections.Counter((r[0],r[2]) for r in rows); print(sorted(c.items(),key=str))
c=collections.Counter((r[0],r[3]) for r in rows); print(sorted(c.items(),key=str))
print([r for r in rows if r[0]][:5])
print([r for r in rows if not r[0]][:8])
