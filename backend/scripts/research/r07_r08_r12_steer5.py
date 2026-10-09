import sys,math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_steer4 import *
def node_err(n,rows,A,sid):
    k=len(n['links']); s=[0.0]*k
    for t,l,ft,x in rows:
        if l<k: s[l]+=ft['eff']*A.get(t,0.05)
    T=sum(s)
    if T<=0: return None
    return max(abs(a/T-b) for a,b in zip(s,n['w']))
def solve(sid,passes=6):
    base,D=build((sid,))
    D=[d for d in D]
    A={t:v for (s,t),v in base.items()}
    # entries without add (type only): unknown strength -> will be fitted from candidates grid
    tags=set(t for _,n,rows in D for t,l,ft,x in rows)
    for t in tags: A.setdefault(t,0.05)
    cands={}
    for t in tags:
        adds=[x['add'] for _,n,rows in D for tt,l,ft,x in rows if tt==t and x.get('add')]
        c=set()
        for a in adds:
            for m in range(1,9): c.add(round(a*m,4))
        if not c: c={0.0,0.01,0.02,0.03,0.05,0.08,0.1}
        cands[t]=sorted(c)
    by_tag={t:[d for d in D if any(tt==t for tt,_,_,_ in d[2])] for t in tags}
    for p in range(passes):
        changed=0
        for t in tags:
            best=None
            for c in cands[t]:
                old=A[t]; A[t]=c
                e=sum((node_err(n,rows,A,sid) or 0)**2 for _,n,rows in by_tag[t])
                A[t]=old
                if best is None or e<best[0]-1e-12: best=(e,c)
            if best[1]!=A[t]: changed+=1; A[t]=best[1]
        if not changed: break
    return A,D
if __name__=='__main__':
    for sid in ('S79','S80'):
        A,D=solve(sid)
        ok=tot=0; ok3=0
        for _,n,rows in D:
            e=node_err(n,rows,A,sid)
            if e is None: continue
            tot+=1; ok+= e<=0.0011; ok3+= e<=0.004
        print(sid,'nodes',tot,'within .0011:',ok,'within .004:',ok3)
