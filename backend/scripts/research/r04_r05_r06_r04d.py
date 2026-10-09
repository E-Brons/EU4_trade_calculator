import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, collections, functools
from app.trade import game_data
g=game_data.graph()
rows,nodes=fl.load()
E=[r for r in rows if set(r)-{'max_demand','sid','node','tag','date'}]
nidx={(n['sid'],n['definitions']):n for n in nodes}
@functools.lru_cache(None)
def down(n):
    s=set()
    for t in g.outgoing(n): s.add(t); s|=down(t)
    return frozenset(s)
def is_collect(r): return bool(r.get('has_capital')) and True or ('total' in r)
bysid=collections.defaultdict(list)
for r in E: bysid[r['sid']].append(r)
bad=[]; tot=0
for sid,rs in bysid.items():
    cn=collections.defaultdict(set)
    for r in rs:
        if r.get('has_trader') and ('total' in r or r.get('has_capital')): cn[r['tag']].add(r['node'])
    pernode=collections.defaultdict(list)
    for r in rs: pernode[r['node']].append(r)
    for node,lst in pernode.items():
        n=nidx[(sid,node)]
        if n.get('pull_power') is None: continue
        tot+=1
        pull=0.0
        for r in lst:
            if 'val' not in r: continue
            coll = 'total' in r or bool(r.get('has_capital') and r.get('has_trader'))
            steer = 'type' in r
            if steer or (not coll and (cn[r['tag']] & down(node))):
                pull += r['val']-r.get('t_out',0)+r.get('t_in',0)
        if abs(pull-n['pull_power'])>0.0015*max(1,len(lst)) and abs(pull-n['pull_power'])>0.01: bad.append((sid,node,round(pull,3),n['pull_power']))
print(tot, len(bad)); print(bad[:12])
for sid,node,p,rec in bad[:4]:
    if sid in ('S79','S80','U01','U02'):
        print(sid,node,[ (r['tag'],r.get('val'),r.get('t_in'),r.get('t_out'),r.get('has_trader'),'total' in r,'type' in r, r.get('has_capital')) for r in bysid[sid] if r['node']==node and r['tag'] in ('POR','BRZ','C04','SPA') ])
