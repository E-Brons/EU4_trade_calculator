"""R13 Q3: residuals of province_power == sum(trade_power of provinces whose controller == tag, province.trade == node)."""
import sys,re,collections
sys.path.insert(0,'scripts/research')
import common
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
st=collections.Counter(); diffs=collections.Counter(); fails=[]; by=collections.Counter()
for e in common.entries():
    prov=common.block(e,'provinces'); ns=common.nodes(e)
    sums=collections.defaultdict(float); cnt=collections.Counter(); provs=collections.defaultdict(list)
    for pid,p in prov.items():
        if not isinstance(p,dict) or 'trade' not in p or p.get('trade_power') is None: continue
        c=p.get('controller')
        if c: sums[(p['trade'],c)]+=p['trade_power']; provs[(p['trade'],c)].append(pid)
    for n in ns:
        nid=n['definitions']
        es={t:v for t,v in n.items() if TAG.match(t) and isinstance(v,dict)}
        for t in set(es)|{tt for (nn,tt) in sums if nn==nid}:
            pp=es.get(t,{}).get('province_power',0.0); s=sums.get((nid,t),0.0)
            if pp>0 or s>0: st['entry-node pairs with power']+=1
            if abs(pp-s)>0.0025:
                st['fail']+=1; by[e['id']]+=1
                diffs[round(pp-s,3)]+=1
                fails.append((e['id'],nid,t,pp,round(s,3),round(pp-s,3)))
print(dict(st)); print('diff histogram', diffs.most_common(12)); print('by save', by.most_common(15))
print('tags',collections.Counter(f[2] for f in fails).most_common(10))
print('nodes',collections.Counter(f[1] for f in fails).most_common(10))
for f in fails[:3]+[x for x in fails if abs(x[5])==1.0][:3]: print(f)
