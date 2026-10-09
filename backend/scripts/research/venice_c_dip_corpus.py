"""Replication: foreign - domestic class == 0.012 + 0.005*ruler DIP for two-class countries, over corpus saves (ruler = history monarch with the country's current monarch id)."""
import sys, collections
sys.path.insert(0,'scripts/research')
import common, venice_c_lib as L
from venice_c_xdip import ruler
tot=collections.Counter(); per={}
for e in common.entries():
    if e['id'] in ('U07',): continue
    try:
        ns=common.nodes(e); cs=common.block(e,'countries')
    except Exception as ex:
        continue
    tab=L.entries_of(ns)
    byc=collections.defaultdict(collections.Counter)
    for (n,t),v in tab.items():
        if 'max_demand' in v: byc[t][v['max_demand']]+=1
    ok=n2=0
    for t,c in byc.items():
        if len(c)!=2 or not isinstance(cs.get(t),dict): continue
        r=ruler(cs[t])
        if not r: continue
        n2+=1
        f=c.most_common(1)[0][0]; d=min(c)
        if abs((f-d)-(0.012+0.005*r['DIP']))<1e-9: ok+=1
    per[e['id']]=(ok,n2)
    tot['ok']+=ok; tot['n']+=n2
print(tot)
for k in ['S01','S10','S30','S50','S67','S78','S79','S80','U03','U06']:
    print(k,per.get(k))
import json; json.dump(per,open('/tmp/eu4research/out/venice_c_dip_corpus.json','w'))
