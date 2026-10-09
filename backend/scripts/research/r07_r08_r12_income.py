import sys, math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_steer1 import *
from collections import Counter, defaultdict
def xint(m,t):
    # money = trunc3(t_true*(1+X)); t given trunc3 -> X in [m/(t+.001)-1, (m+.001)/t - 1]
    return (m/(t+0.001)-1, (m+0.001)/t-1)
def rows():
    for e,ns in all_saves():
        for n in ns:
            for t,x in n['ents'].items():
                if 'money' in x and 'total' in x and f(x['total'],0)>0:
                    yield e,n,t,x
if __name__=='__main__':
    c=Counter(); pairs=defaultdict(list)
    for e,n,t,x in rows():
        pairs[(e['id'],t)].append((n['id'],x))
    out=Counter(); examples=[]
    for (sid,t),L in pairs.items():
        home=[(nid,x) for nid,x in L if x.get('has_capital')]
        away=[(nid,x) for nid,x in L if not x.get('has_capital') and x.get('has_trader')]
        if len(home)!=1 or not away: continue
        hn,hx=home[0]
        if f(hx['total'])<3: continue
        hlo,hhi=xint(f(hx['money']),f(hx['total']))
        for an,ax in away:
            if f(ax['total'])<3: continue
            alo,ahi=xint(f(ax['money']),f(ax['total']))
            dlo,dhi=alo-hhi,ahi-hlo   # possible range of Xaway-Xhome
            hm='home_merchant' if hx.get('has_trader') else 'home_no_merchant'
            cls=('+0.10' if dlo<=0.10<=dhi else '')+('0.00' if dlo<=0<=dhi else '')
            out[(hm,cls or 'other')]+=1
            if cls=='' and len(examples)<8: examples.append((sid,t,hn,an,round(dlo,3),round(dhi,3)))
    for k,v in sorted(out.items()): print(k,v)
    print(examples)
