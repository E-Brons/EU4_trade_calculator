import sys, math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_steer1 import *
from collections import defaultdict
def build(saves=('S79','S80')):
    base={}; D=[]
    for e,ns in all_saves():
        if e['id'] not in saves: continue
        for n in ns:
            for t,x in n['ents'].items():
                if 'add' in x: base[(e['id'],t)]=max(base.get((e['id'],t),0),x['add'])
        for n in ns:
            if len(n['links'])<2 or not n['raw'].get('outgoing'): continue
            rows=[(t,link_of(x),feats(x),x) for t,x in n['ents'].items() if 'val' in x and ('type' in x or 'add' in x)]
            if rows: D.append((e['id'],n,rows))
    return base,D
def ev(D,name,g,quiet=False):
    err=0;cnt=0;ex=0
    for sid,n,rows in D:
        k=len(n['links']); s=[0.0]*k
        for t,l,ft,x in rows:
            if l<k: s[l]+=g(sid,t,ft,x)
        T=sum(s)
        if T<=0: continue
        d=max(abs(a/T-b) for a,b in zip(s,n['w']))
        err+=d*d;cnt+=1;ex+=d<=0.0011
    if not quiet: print(name, 'rmse',round(math.sqrt(err/cnt),4), 'exact',ex, 'of',cnt)
    return ex,cnt
if __name__=='__main__':
    base,D=build()
    ev(D,'val',lambda sid,t,ft,x:ft['val'])
    ev(D,'eff',lambda sid,t,ft,x:ft['eff'])
    ev(D,'val*base',lambda sid,t,ft,x:ft['val']*base.get((sid,t),0.05))
    ev(D,'eff*base',lambda sid,t,ft,x:ft['eff']*base.get((sid,t),0.05))
    ev(D,'val*add_own',lambda sid,t,ft,x:ft['val']*(x.get('add') or 0.01))
    ev(D,'mp*base',lambda sid,t,ft,x:ft['mp']*base.get((sid,t),0.05))
