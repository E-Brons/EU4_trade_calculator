import sys
sys.path.insert(0,'scripts/research')
import venice_load as V
from venice_load import as_list

def flat(o, pre=''):
    out={}
    if isinstance(o,dict):
        for k,v in o.items(): out.update(flat(v,pre+'/'+str(k)))
    elif isinstance(o,list):
        for i,v in enumerate(o): out.update(flat(v,pre+f'[{i}]'))
    else: out[pre]=o
    return out

def nodeflat(p):
    d={}
    for n in V.nodes(p):
        d.update(flat(n,n['definitions']))
    return d

if __name__=='__main__':
    fs=V.files(); prev=None
    for p in fs:
        cur=nodeflat(p)
        if prev is not None:
            keys=set(cur)|set(prev[1])
            diff=[k for k in keys if cur.get(k)!=prev[1].get(k)]
            nodes=len({k.split('/')[0] for k in diff})
            print(f"{prev[0]} -> {p.stem[6:]}: {len(diff)} fields in {nodes} nodes")
        prev=(p.stem[6:],cur)
