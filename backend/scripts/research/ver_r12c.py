import sys; sys.path.insert(0, 'scripts/research')
from collections import Counter
from ver_common import *
def run(ids):
    C=Counter(); miss=[]
    for sid in ids:
        ns=nodes_of(sid); by={n[0]:n for n in ns}
        for nid,raw,ents in ns:
            inc_sum=sum(fl(i['value']) for i in lst(raw.get('incoming')) if isinstance(i,dict))
            sv=0.0
            for tag,e in ents.items():
                if all(k in e for k in ('val','max_pow','max_demand')):
                    C['val_n']+=1; C['val_ok']+= abs(tr3(e['max_pow']*e['max_demand'])-e['val'])<=0.0011; sv+=e['val']
                if 'max_pow' in e:
                    s_sum=0.0; s_per=0.0
                    for t in [o['target'] for o in GRAPH.get(nid,{}).get('outgoing',[])]:
                        if t in by:
                            pp=fl(by[t][2].get(tag,{}).get('province_power'),0.0)
                            if pp>=10: s_sum+=pp; s_per+=tr3(pp/5)
                    pv=fl(e.get('prev'),0.0)
                    C['prev_n']+=1
                    C['prev_trunc_of_sum']+= abs(tr3(s_sum/5)-pv)<=0.0011
                    C['prev_sum_of_trunc']+= abs(s_per-pv)<=0.0011
                    if abs(s_per-pv)>0.0011: miss.append((sid,nid,tag,pv,round(s_per,3)))
            if 'total' in raw and sv>0:
                C['tot_n']+=1; C['tot_eq_sumval_0.01']+= abs(raw['total']-sv)<=0.01
            if all(k in raw for k in ('current','local_value','retention')):
                C['cur_n']+=1; C['cur_ok_0.0015']+= abs((raw['local_value']+inc_sum)*raw['retention']-raw['current'])<=0.0015
            if all(k in raw for k in ('outgoing','current','local_value')):
                C['out_n']+=1; C['out_ok_0.0015']+= abs(raw['local_value']+inc_sum-raw['current']-raw['outgoing'])<=0.0015
            if all(k in raw for k in ('retention','retain_power','pull_power')) and raw['retain_power']+raw['pull_power']>0:
                C['ret_n']+=1; C['ret_ok_0.0011']+= abs(raw['retain_power']/(raw['retain_power']+raw['pull_power'])-raw['retention'])<=0.0011
    return C,miss
for label,ids in (('start78',STARTS),('played S79+S80',list(PLAYED))):
    C,m=run(ids); print(label,dict(C))
    if label.startswith('played'): print(' prev misses (sum of trunc)',m)
    else: print(' first prev misses',m[:4], len(m))
