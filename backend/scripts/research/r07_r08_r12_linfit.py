import sys, math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_steer1 import *
def jacobi(A, iters=200):
    n=len(A); V=[[float(i==j) for j in range(n)] for i in range(n)]; A=[r[:] for r in A]
    for _ in range(iters):
        p=q=0; mx=0
        for i in range(n):
            for j in range(i+1,n):
                if abs(A[i][j])>mx: mx=abs(A[i][j]); p,q=i,j
        if mx<1e-14: break
        th=0.5*math.atan2(2*A[p][q],A[q][q]-A[p][p]); c,s=math.cos(th),math.sin(th)
        for k in range(n):
            akp,akq=A[k][p],A[k][q]; A[k][p]=c*akp-s*akq; A[k][q]=s*akp+c*akq
        for k in range(n):
            apk,aqk=A[p][k],A[q][k]; A[p][k]=c*apk-s*aqk; A[q][k]=s*apk+c*aqk
        for k in range(n):
            vkp,vkq=V[k][p],V[k][q]; V[k][p]=c*vkp-s*vkq; V[k][q]=s*vkp+c*vkq
    ev=[A[i][i] for i in range(n)]
    return ev,V
def fit(rows_fn, names, saves=('S79','S80'), select=lambda x:'type' in x):
    M=[]
    for e,ns in all_saves():
        if e['id'] not in saves: continue
        for n in ns:
            if len(n['links'])<2 or not n['raw'].get('outgoing') or min(n['w'])<0: continue
            k=len(n['links']); F=[[0.0]*len(names) for _ in range(k)]
            any_=False
            for t,x in n['ents'].items():
                if 'val' in x and select(x):
                    l=link_of(x)
                    if l<k:
                        v=rows_fn(x)
                        for a in range(len(names)): F[l][a]+=v[a]
                        any_=True
            if not any_: continue
            for j in range(1,k):
                if n['w'][0]==0 and n['w'][j]==0: continue
                M.append([F[0][a]*n['w'][j]-F[j][a]*n['w'][0] for a in range(len(names))])
    n=len(names)
    A=[[sum(r[i]*r[j] for r in M) for j in range(n)] for i in range(n)]
    ev,V=jacobi(A)
    idx=sorted(range(n),key=lambda i:ev[i])
    print('rows',len(M))
    for i in idx[:2]:
        v=[V[k][i] for k in range(n)]
        s=max(v,key=abs); v=[x/s for x in v]
        print('eig',round(ev[i],4),dict(zip(names,[round(x,4) for x in v])))
if __name__=='__main__':
    def r1(x):
        ft=feats(x); return [ft['val'],ft['mp'],ft['pp'],ft['prev'],f(x.get('t_out'),0),f(x.get('t_in'),0),1.0]
    fit(r1,['val','mp','pp','prev','t_out','t_in','one'])
    def r2(x):
        ft=feats(x); return [ft['val'],ft['mp']]
    fit(r2,['val','mp'])
    def r3(x):
        ft=feats(x); return [ft['eff'],1.0]
    fit(r3,['eff','one'])
