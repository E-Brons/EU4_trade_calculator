"""Does the home income efficiency X (money/total at the has_capital node) follow the ruler's skills? (U07, 1444.11.11)"""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_load as V
import venice_c_lib as L

def ruler(c):
    """History `monarch` block whose id equals the country's current monarch id."""
    h=c.get('history'); cur=c.get('monarch')
    cid=(cur.get('id') if isinstance(cur,dict) else None)
    cid=cid.get('id') if isinstance(cid,dict) else cid
    if not isinstance(h,dict) or cid is None: return None
    for k,v in h.items():
        for x in L.as_list(v):
            if isinstance(x,dict) and 'monarch' in x:
                for m in L.as_list(x['monarch']):
                    if isinstance(m,dict) and 'DIP' in m:
                        mid=m.get('id'); mid=mid.get('id') if isinstance(mid,dict) else mid
                        if mid==cid: return m
    return None

if __name__=='__main__':
    p=V.files()[0]
    cu=V.load(p,'countries'); ns=V.nodes(p)
    X={}
    for n in ns:
        for k,v in n.items():
            if isinstance(v,dict) and v.get('has_capital') and v.get('total',0)>=0.5 and 'money' in v:
                X[k]=v['money']/v['total']
    rows=[]
    for t,x in X.items():
        c=cu.get(t)
        if not isinstance(c,dict): continue
        r=ruler(c)
        g=c.get('government'); refs=tuple((g or {}).get('reform_stack',{}).get('reforms',[])[-1:]) if isinstance(g,dict) else ()
        if r: rows.append((refs,round(x,2),r['ADM'],r['DIP'],r['MIL'],t,c.get('technology',{}).get('dip_tech') if isinstance(c.get('technology'),dict) else None))
    print(len(X),len(rows))
    grp=collections.defaultdict(list)
    for r in rows: grp[r[0]].append(r)
    for k,v in sorted(grp.items(),key=lambda kv:-len(kv[1]))[:4]:
        print(k,len(v))
        bydip=collections.defaultdict(collections.Counter)
        for r in v: bydip[r[3]][r[1]]+=1
        print('  X by ruler DIP:',{d:dict(c) for d,c in sorted(bydip.items())})
        byadm=collections.defaultdict(collections.Counter)
        for r in v: byadm[r[2]][r[1]]+=1
        print('  X by ruler ADM:',{d:dict(c) for d,c in sorted(byadm.items())})
