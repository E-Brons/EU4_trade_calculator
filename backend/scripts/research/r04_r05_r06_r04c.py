import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, collections, math
rows, nodes = fl.load()
nidx = {(n['sid'], n['definitions']): n for n in nodes}
E = [r for r in rows if 'potential' in r and nidx[(r['sid'],r['node'])].get('total')]
print('potential entries in nodes without total:', sum(1 for r in rows if 'potential' in r and not nidx[(r['sid'],r['node'])].get('total')))
nt=[r for r in E if not r.get('t_out') and not r.get('t_in')]
print('potential entries without transfer:', len(nt), 'nonzero', sum(1 for r in nt if r['potential']!=0), collections.Counter(round(r['potential'],3) for r in nt).most_common(6))
print('entries with potential', len(E), 'with t_out>0', sum(1 for r in E if r.get('t_out',0)>0), 't_in>0', sum(1 for r in E if r.get('t_in',0)>0), 'both', sum(1 for r in E if r.get('t_out',0)>0 and r.get('t_in',0)>0))
print('entries with t_out or t_in but no potential', sum(1 for r in rows if (r.get('t_out',0)>0 or r.get('t_in',0)>0) and 'potential' not in r))
tr = lambda x: math.trunc(x*1000+1e-9)/1000
fl_ = lambda x: math.floor(x*1000+1e-9)/1000
rd = lambda x: math.floor(x*1000+0.5)/1000
V = {'trunc toward 0': tr, 'floor': fl_, 'round': rd}
for n,f in V.items():
    ok = sum(1 for r in E if abs(f((r.get('t_out',0)-r.get('t_in',0))/nidx[(r['sid'],r['node'])]['total'])-r['potential'])<1e-9)
    print(n, ok, 'of', len(E))
# with total denominators alternatives
for alt in ('retain_power','collector_power'):
    ok = sum(1 for r in E if nidx[(r['sid'],r['node'])].get(alt) and abs(tr((r.get('t_out',0)-r.get('t_in',0))/nidx[(r['sid'],r['node'])][alt])-r['potential'])<1e-9)
    print('denominator', alt, ok)
# sign: receivers negative, givers positive
print('sign check: givers potential>0', sum(1 for r in E if r.get('t_out',0)>0 and r['potential']>0), 'receivers potential<0', sum(1 for r in E if r.get('t_in',0)>0 and r['potential']<0), 'other potential!=0', sum(1 for r in E if not r.get('t_out') and not r.get('t_in') and r['potential']!=0))
print('potential==0 with t', sum(1 for r in E if (r.get('t_out') or r.get('t_in')) and r['potential']==0))
# negative values where trunc toward 0 vs floor differ
diff=[r for r in E if abs(tr((r.get('t_out',0)-r.get('t_in',0))/nidx[(r['sid'],r['node'])]['total'])-fl_((r.get('t_out',0)-r.get('t_in',0))/nidx[(r['sid'],r['node'])]['total']))>1e-9]
print('entries where trunc!=floor (negative non-exact)', len(diff), 'of which trunc matches', sum(1 for r in diff if abs(tr((r.get('t_out',0)-r.get('t_in',0))/nidx[(r['sid'],r['node'])]['total'])-r['potential'])<1e-9))

print('=== potential in nodes without total')
X=[r for r in rows if 'potential' in r and not nidx[(r['sid'],r['node'])].get('total')]
print(len(X), collections.Counter(round(r['potential'],4) for r in X).most_common(8))
print(collections.Counter(r['node'] for r in X).most_common(8), collections.Counter(r['sid'] for r in X).most_common(3))
print(sorted(set(k for r in X for k in r))[:30])
n=nidx[(X[0]['sid'],X[0]['node'])]; print({k:v for k,v in n.items() if k not in ('order','top_power','top_power_values','top_provinces','top_provinces_values','trade_goods_size')})
print('with t_in/t_out', sum(1 for r in X if r.get('t_in') or r.get('t_out')), ' with only potential+max_demand', sum(1 for r in X if set(r)-{'sid','node','tag','date'}=={'potential','max_demand'}))
