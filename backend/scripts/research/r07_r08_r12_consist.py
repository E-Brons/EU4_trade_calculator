import sys, math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_steer1 import *
from collections import Counter
def fx(x): return math.trunc(x*1000+1e-9)/1000
kinds={e['id']:e.get('kind','start') for e in common.entries()}
agg={}
for e,ns in all_saves():
    c=agg.setdefault(kinds[e['id']],Counter())
    for n in ns:
        r=n['raw']
        # entry level
        sv=0.0
        for t,x in n['ents'].items():
            if 'val' in x and 'max_pow' in x and 'max_demand' in x:
                c['val_checked']+=1; c['val_ok']+= abs(fx(x['max_pow']*x['max_demand'])-x['val'])<=0.0011
                sv+=x['val']
        if 'total' in r and sv>0:
            c['total_checked']+=1; c['total_eq_sum_val(+-.01)']+= abs(r['total']-sv)<=0.01
        if all(k in r for k in ('current','local_value','retention')):
            inc=sum(v for _,v,_ in n['incoming'])
            c['current_checked']+=1; c['current_ok(+-.0015)']+= abs((r['local_value']+inc)*r['retention']-r['current'])<=0.0015+0.0015*abs(r['current'])*0
        if all(k in r for k in ('retention','retain_power','pull_power')):
            T=r['retain_power']+r['pull_power']
            if T>0:
                c['retention_checked']+=1; c['retention_ok(+-.0011)']+= abs(r['retain_power']/T-r['retention'])<=0.0011
        if all(k in r for k in ('outgoing','current','local_value')):
            inc=sum(v for _,v,_ in n['incoming'])
            c['gross_checked']+=1; c['outgoing==gross-current(+-.0015)']+= abs((r['local_value']+inc-r['current'])-r['outgoing'])<=0.0015
for k,a in agg.items(): print(k,dict(a))
