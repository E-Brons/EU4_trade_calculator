import sys, math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_steer1 import *
from collections import Counter, defaultdict
def run(verbose=False):
    S=Counter(); worst=[]
    for e,ns in all_saves():
        by={n['id']:n for n in ns}
        for n in ns:
            out=f(n['raw'].get('outgoing'))
            if not n['links'] or out is None: continue
            k=len(n['links'])
            w=n['w'] if len(n['w'])==k else None
            incs=[]
            for i,t in enumerate(n['links']):
                inc=[(v,a) for s,v,a in by[t]['incoming'] if s==n['id']]
                incs.append(inc[0] if len(inc)==1 else None)
                if len(inc)!=1: S['inc_count_not_1']+=1
            if any(x is None for x in incs): continue
            tot=sum(v for v,a in incs); addsum=sum(a for v,a in incs)
            S['nodes']+=1
            diff=tot-out
            S['sum_eq_out(+-0.0015)']+= abs(diff)<=0.0015*max(1,k)
            S['sum_minus_out_eq_sum_add(+-.0015k)']+= abs(diff-addsum)<=0.0015*max(1,k)
            S['has_add']+= addsum>0
            if abs(diff)>0.0015*max(1,k): S['mismatch']+=1
            if abs(diff)>0.0015*max(1,k) and abs(diff-addsum)>0.0015*max(1,k)+0.001: S['mismatch_not_explained_by_add']+=1; worst.append((e['id'],n['id'],out,tot,addsum))
            S['vao==out']+= abs((f(n['raw'].get('value_added_outgoing'),out))-out)<=0.0005
            S['vao_present']+= 'value_added_outgoing' in n['raw']
            if w:
                for i,(v,a) in enumerate(incs):
                    S['links']+=1
                    S['value-add==out*w (tol .0015+.0006out)']+= abs((v-a)-out*w[i])<=0.0015+0.0006*out
                    # add vs out*w*sum(add of steerers on link i)
                    sa=sum(f(x.get('add'),0) for x in n['ents'].values() if 'type' in x and link_of(x)==i)
                    S['add==out*w*sum(add) (tol .0015+..)']+= abs(a-out*w[i]*sa)<=0.0015+0.0006*out+0.01*abs(a)
    return S,worst
if __name__=='__main__':
    S,w=run()
    for k,v in S.items(): print(k,v)
    print(w[:15])
