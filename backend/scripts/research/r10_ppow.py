import sys, os, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
c=collections.Counter(); ex=[]
for e in common.entries():
    for n in common.nodes(e):
        ents={k:v for k,v in n.items() if TAG.match(k) and isinstance(v,dict)}
        if n.get('total') is None or 'p_pow' not in n or 'max' not in n: continue
        sv=sum(v.get('val',0) for v in ents.values())
        sprov=sum(v.get('province_power',0) for v in ents.values())
        sship=sum(v.get('ship_power',0) for v in ents.values())
        gap=n['total']-sv
        dpp=n['p_pow']-sprov
        key=('gap>0' if gap>0.0015 else 'gap0', 'dpp==0' if abs(dpp)<0.0035 else 'dpp!=0')
        c[key]+=1
        if key==('gap>0','dpp!=0') and len(ex)<12: ex.append((e['id'],n['definitions'],round(gap,3),round(dpp,3), round(gap/dpp,3) if dpp else None, round(n['max']-n['p_pow']-sship,3) if 'max' in n else None))
        if key==('gap0','dpp!=0') and len(ex)<12: ex.append(('GAP0',e['id'],n['definitions'],round(dpp,3)))
print(c)
for x in ex: print(x)
