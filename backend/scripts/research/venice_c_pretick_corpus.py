"""Start snapshots (kind start): collecting merchants away from the capital node, with/without money and max_demand halving."""
import sys, collections
sys.path.insert(0,'scripts/research')
import common, venice_c_lib as L
tot=collections.Counter()
for e in common.entries():
    if e.get('kind')!='start': continue
    try: ns=common.nodes(e)
    except Exception: continue
    cls=collections.defaultdict(collections.Counter)
    for n in ns:
        for k,v in n.items():
            if isinstance(v,dict) and L.TAGLIKE(k) and 'max_demand' in v: cls[k][v['max_demand']]+=1
    for n in ns:
        for k,v in n.items():
            if isinstance(v,dict) and L.TAGLIKE(k) and v.get('has_trader') and 'type' not in v and not v.get('has_capital'):
                tot['away collecting merchant entries']+=1
                tot['  with money']+= 'money' in v
                base=max(cls[k],key=lambda c: cls[k][c])
                tot['  md equals a class value (not halved)']+= any(abs(v['max_demand']-c)<0.0011 for c in cls[k])
                tot['  md == half of the mode']+= abs(v['max_demand']-base/2)<0.0011
    tot['saves']+=1
print(dict(tot))
