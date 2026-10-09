import sys, math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_steer1 import *
def dataset(saves=('S79','S80'), only_type=True):
    D=[]
    for e,ns in all_saves():
        if e['id'] not in saves: continue
        for n in ns:
            if len(n['links'])<2 or not n['raw'].get('outgoing'): continue
            rows=[]
            for t,x in n['ents'].items():
                if 'val' in x and ('type' in x):
                    rows.append((link_of(x),feats(x),x))
            if rows: D.append((e['id'],n,rows))
    return D
def evaluate(D,g):
    err=0;cnt=0;exact=0
    for sid,n,rows in D:
        k=len(n['links']); s=[0.0]*k
        for l,ft,x in rows:
            if l<k: s[l]+=g(ft,x)
        T=sum(s)
        if T<=0: continue
        d=max(abs(a/T-b) for a,b in zip(s,n['w']))
        err+=d*d; cnt+=1; exact+= d<=0.0011
    return math.sqrt(err/cnt), exact, cnt
if __name__=='__main__':
    D=dataset()
    print('val',evaluate(D,lambda ft,x:ft['val']))
    print('eff',evaluate(D,lambda ft,x:ft['eff']))
    for p in (0.9,1.0,1.1,1.2,1.3):
        print('eff^p',p,evaluate(D,lambda ft,x:max(ft['eff'],0)**p))
    for eps in (-2,-1,-0.5,0,0.5,1,2,5):
        print('eff+eps',eps,evaluate(D,lambda ft,x:max(ft['eff']+eps,0)))
