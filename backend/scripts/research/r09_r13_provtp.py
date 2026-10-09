"""R13 Q4: structure of a province's stored trade_power: tp = (0.2*dev + cot_flat) * M * (1 - 0.005*autonomy); M per (controller,node)?"""
import sys,re,collections,statistics
sys.path.insert(0,'scripts/research')
import common
SAVES=sys.argv[1:] or ['S14']
COT={None:0,1:5,2:10,3:25}
for e in [x for x in common.entries() if x['id'] in SAVES]:
    prov=common.block(e,'provinces')
    groups=collections.defaultdict(list); skipped=collections.Counter()
    for pid,p in prov.items():
        if not isinstance(p,dict) or 'trade' not in p or p.get('trade_power') is None or not p.get('owner'): continue
        if p.get('controller')!=p.get('owner'): skipped['controller != owner']+=1; continue
        dev=p.get('base_tax',0)+p.get('base_production',0)+p.get('base_manpower',0)
        base=0.2*dev+COT.get(p.get('center_of_trade'),float('nan'))
        if base<=0: skipped['base 0']+=1; continue
        aut=p.get('local_autonomy',0.0)
        m=p['trade_power']/(base*(1-0.005*aut))
        key=(p['trade'],p['owner'])
        groups[key].append((round(m,3),pid,p.get('buildings') and sorted(p['buildings']),dev,p.get('center_of_trade'),aut,p['trade_power'],bool(p.get('trade_company'))))
    n=len(groups); const=0; varying=[]
    for k,v in groups.items():
        ms={x[0] for x in v}
        if max(ms)-min(ms)<=0.01: const+=1
        else: varying.append((k,sorted(ms)[:5]))
    nprov=sum(len(v) for v in groups.values()); single=sum(1 for v in groups.values() if len(v)==1)
    print(e['id'],'(node,owner) groups',n,'provinces',nprov,'groups with identical multiplier M (spread<=0.01):',const,'of which single-province groups',single,'skipped',dict(skipped))
    print(' varying examples',varying[:6])
    allm=collections.Counter(x[0] for v in groups.values() for x in v)
    print(' most common M values (province count)',allm.most_common(8))
