"""R13 Q1 follow-up: incense; nodes still off without incense; which index mismatches total_produced."""
import sys,json,collections
sys.path.insert(0,'scripts/research')
import common
def al(x): return x if isinstance(x,list) else [x]
pr=json.load(open('/tmp/eu4research/out/_prices_by_save.json'))
names=list(pr['S01'])
print('incense current_price in save by save id (distinct):',collections.Counter(pr[s]['incense'] for s in pr))
off_noinc=collections.Counter(); offs=[]; tot=0; incnodes=0; fit=collections.Counter()
mm=collections.Counter()
import re
for e in common.entries():
    sid=e['id']; price=[pr[sid][n] for n in names]
    t=common._text(e).gamestate
    m=re.search(r'\ntradegoods_total_produced=\{\s*([^}]*)\}',t); prod=[float(x) for x in m.group(1).split()]
    ns=[n for n in common.nodes(e) if 'trade_goods_size' in n]
    sums=[sum(al(n['trade_goods_size'])[k] for n in ns) for k in range(33)]
    for k,(a,b) in enumerate(zip(sums,prod)):
        if abs(a-b)>0.05: mm[(names[k],round(a-b,3))]+=1
    for n in ns:
        if 'local_value' not in n: continue
        sz=al(n['trade_goods_size'])
        pred=sum(s*price[k] for k,s in enumerate(sz))/12
        d=n['local_value']-pred; tot+=1
        inc=sz[names.index('incense')]
        if abs(d)>0.002:
            if inc>0:
                incnodes+=1
                fit[round(d/inc*12,3)]+=1
            else:
                off_noinc[sid]+=1; offs.append((sid,n['definitions'],n['local_value'],round(pred,3)))
print('nodes',tot,'off with incense',incnodes,'implied extra price*12 per incense unit (value:count)',fit.most_common(6))
print('off without incense',sum(off_noinc.values()),dict(off_noinc)); print(offs[:12])
print('total_produced mismatches (good, sum(size)-total_produced):',mm.most_common(5))
