import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, collections, math
rows,nodes=fl.load()
nidx={(n['sid'],n['definitions']):n for n in nodes}
tr=lambda x: math.trunc(x*1000+1e-9)/1000
P=[r for r in rows if 'power_fraction' in r]
c=collections.Counter(); fails=[]
for r in P:
    n=nidx[(r['sid'],r['node'])]; rp=n.get('retain_power')
    eff=r['val']-r.get('t_out',0)+r.get('t_in',0)
    kind='giver' if r.get('t_out') else ('receiver' if r.get('t_in') else 'plain')
    ok=rp and abs(tr(eff/rp)-r['power_fraction'])<1e-9
    c[(kind,bool(ok))]+=1
    if not ok and kind!='plain': fails.append((r['sid'],r['node'],r['tag'],kind,r['power_fraction'],round(eff/rp,5) if rp else None))
print(len(P), dict(c)); print(fails[:8])
# alternative for givers: (val - t_out)/retain
g=[r for r in P if r.get('t_out')]
print('giver val/ retain', sum(1 for r in g if abs(tr(r['val']/nidx[(r['sid'],r['node'])]['retain_power'])-r['power_fraction'])<1e-9), 'of', len(g))
# receivers collecting: t_in in the collector's power
rc=[r for r in P if r.get('t_in')]; print('collecting receivers', len(rc), [ (r['sid'],r['node'],r['tag']) for r in rc][:5])
# the goal's C03 example: find entries with t_out ~334.426
for r in P:
    if r.get('t_out') and abs(r['t_out']-334.426)<0.002: print(r['sid'],r['node'],r['tag'],r['val'],r['t_out'],r['power_fraction'],nidx[(r['sid'],r['node'])]['retain_power'])
# 'total' (income share) = trunc3(current*power_fraction) for receivers/givers
cc=collections.Counter()
for r in P:
    n=nidx[(r['sid'],r['node'])]
    if 'total' in r and n.get('current') is not None:
        kind='giver' if r.get('t_out') else ('receiver' if r.get('t_in') else 'plain')
        cc[(kind, abs(tr(n['current']*r['power_fraction'])-r['total'])<1e-9)]+=1
print(dict(cc))
