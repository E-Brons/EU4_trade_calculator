"""R13 Q1: local_value == sum(trade_goods_size[i] * current_price[i]) / 12 with current_price read from the save's top-level change_price block
(order of the keys = index of trade_goods_size); also tradegoods_total_produced vs trade_goods_size."""
import sys,re,collections,json
sys.path.insert(0,'scripts/research')
import common
def al(x): return x if isinstance(x,list) else [x]
tot=collections.Counter(); out={}
for e in common.entries():
    t=common._text(e).gamestate
    i=t.find('\nchange_price={')
    j=t.find('\n}\n',i)
    blk=t[i:j]
    goods=re.findall(r'\n\t(\w+)=\{\n\t\tcurrent_price=([-\d.]+)',blk)
    names=[g for g,_ in goods]; price=[float(p) for _,p in goods]
    m=re.search(r'\ntradegoods_total_produced=\{\s*([^}]*)\}',t); prod=[float(x) for x in m.group(1).split()] if m else None
    nodes=common.nodes(e); n_=0; bad=0; mx=0; worst=None; sizebad=0
    for n in nodes:
        if 'trade_goods_size' not in n or 'local_value' not in n: continue
        sz=al(n['trade_goods_size']); pred=sum(s*price[k] for k,s in enumerate(sz))/12
        d=abs(pred-n['local_value']); n_+=1
        if d>mx: mx=d; worst=(n['definitions'],n['local_value'],round(pred,3))
        bad+= d>0.002
    # tradegoods_total_produced == sum of sizes across nodes?
    if prod:
        sums=[sum(al(n['trade_goods_size'])[k] for n in nodes if 'trade_goods_size' in n) for k in range(33)]
        sizebad=sum(abs(a-b)>0.05 for a,b in zip(sums,prod))
    print(e['id'],len(names),'goods in change_price; nodes',n_,'max err',round(mx,4),'off>0.002:',bad,worst if bad else '','| total_produced vs sum(size) mismatching indices:',sizebad, flush=True)
    tot['nodes']+=n_; tot['off']+=bad
    out[e['id']]=dict(zip(names,price))
print(dict(tot)); print(names)
json.dump(out,open('/tmp/eu4research/out/_prices_by_save.json','w'))
