"""Two-class countries in U07: foreign minus domestic class value vs ruler DIP, grouped by whether it equals 0.012+0.005*DIP."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_c_lib as L, venice_load as V
from venice_c_xdip import ruler
p=V.files()[0]; cu=V.load(p,'countries'); tab=L.entries_of(V.nodes(p))
byc=collections.defaultdict(collections.Counter)
for (n,t),e in tab.items():
    if 'max_demand' in e: byc[t][e['max_demand']]+=1
fit=collections.Counter(); other=[]
for t,c in byc.items():
    if len(c)!=2 or not isinstance(cu.get(t),dict): continue
    r=ruler(cu[t])
    if not r: fit['no ruler']+=1; continue
    f=c.most_common(1)[0][0]; d=min(c); 
    g=cu[t].get('government'); g=g.get('government') if isinstance(g,dict) else g
    ok=abs((f-d)-(0.012+0.005*r['DIP']))<1e-9
    fit[ok]+=1
    if not ok: other.append((t,round(f-d,3),r['DIP'],g,cu[t].get('technology_group'),d,f))
print(fit)
print(other[:25])
