"""R09 Q1/Q3/Q5 support: extras distribution, max_demand range, worked example rows (S14 alexandria)."""
import sys,re,collections,math
sys.path.insert(0,'scripts/research')
import common
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
ex=collections.Counter(); md=[]; mdtur=[]
for e in common.entries():
    for n in common.nodes(e):
        for t,v in n.items():
            if not(TAG.match(t) and isinstance(v,dict)): continue
            if 'max_demand' in v: md.append(v['max_demand'])
            if 'max_pow' in v:
                ex[round(v['max_pow']-v.get('province_power',0)-v.get('ship_power',0)-v.get('prev',0),3)]+=1
            if e['id']=='S14' and t=='TUR' and 'max_demand' in v: mdtur.append((n['definitions'],v['max_demand']))
print('max_demand min/max/n',min(md),max(md),len(md),'below 1.0:',sum(x<1 for x in md),'above 2:',sum(x>2 for x in md))
tot=sum(ex.values()); print('entries with max_pow',tot,'extras values (top 14):',ex.most_common(14)); print('extras not in {0,5}:',tot-ex[0.0]-ex[5.0])
print('TUR S14 max_demand across nodes: distinct',len({x[1] for x in mdtur}),'min',min(mdtur,key=lambda x:x[1]),'max',max(mdtur,key=lambda x:x[1]))
e=[x for x in common.entries() if x['id']=='S14'][0]
fx=lambda x: math.trunc(x*1000+1e-9)/1000
for n in common.nodes(e):
    if n['definitions']=='alexandria':
        es={t:v for t,v in n.items() if TAG.match(t) and isinstance(v,dict)}
        coll={t:v for t,v in es.items() if 'total' in v}
        eff=lambda v: v.get('val',0)-v.get('t_out',0)+v.get('t_in',0)
        pull_tags=[t for t,v in es.items() if 'type' in v]
        print('alexandria node:',{k:n[k] for k in ('local_value','current','outgoing','retention','retain_power','pull_power','total','p_pow','max','highest_power','collector_power','num_collectors','num_collectors_including_pirates') if k in n})
        print(' incoming',n['incoming'],'steer_power',n['steer_power'])
        print(' collectors',{t:{k:v[k] for k in ('province_power','prev','max_pow','max_demand','val','power_fraction','total','money','has_capital','has_trader') if k in v} for t,v in coll.items()})
        print(' sum retain (val-tout+tin collectors)',round(sum(eff(v) for v in coll.values()),3),'sum val all',round(sum(v.get('val',0) for v in es.values()),3),'sum province_power',round(sum(v.get('province_power',0) for v in es.values()),3),'sum(max_pow-prev)',round(sum(v['max_pow']-v.get('prev',0) for v in es.values() if 'max_pow' in v),3))
        print(' retention check', round(n['retain_power']/(n['retain_power']+n['pull_power']),4), 'current check',round((n['local_value']+sum(i['value'] for i in n['incoming']))*n['retention'],3))
        print(' top_power',list(zip(n['top_power'],n['top_power_values']))[:4],' top_provinces',list(zip(n['top_provinces'],n['top_provinces_values']))[:3])
        for t in list(coll)[:3]:
            v=coll[t]; print('  ',t,'power_fraction fx(eff/retain)',fx(eff(v)/n['retain_power']),'stored',v['power_fraction'],'| total fx(current*pf)',fx(n['current']*v['power_fraction']),'stored',v['total'], '| val fx(max_pow*max_demand)',fx(v['max_pow']*v['max_demand']),'stored',v['val'])
