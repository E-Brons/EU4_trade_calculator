import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_load import *
from r07_r08_r12_steer1 import feats, link_of
from functools import lru_cache
@lru_cache(None)
def reach(node):
    s={node}
    for t in OUT.get(node,[]): s|=reach(t)
    return frozenset(s)
def analyse(ns, eff_q='eff'):
    col={}
    for n in ns:
        for t,x in n['ents'].items():
            if 'total' in x: col.setdefault(t,set()).add(n['id'])
    out=[]
    for n in ns:
        if len(n['links'])<2 or not n['w'] or not n['raw'].get('outgoing'): continue
        pullers=[]
        for t,x in n['ents'].items():
            if 'val' not in x or 'total' in x: continue
            q=feats(x)[eff_q]
            if 'type' in x:
                pullers.append((t,q,{link_of(x)},'steer'))
            else:
                ls={i for i,l in enumerate(n['links']) if reach(l)&col.get(t,set())}
                if ls: pullers.append((t,q,ls,'pull'))
        out.append((n,pullers))
    return out
