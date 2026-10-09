import sys, os, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
c=collections.Counter(); ex=[]
stat=collections.defaultdict(list)
for e in common.entries():
    for n in common.nodes(e):
        ents={k:v for k,v in n.items() if TAG.match(k) and isinstance(v,dict)}
        if n.get('total') is None or 'max' not in n:
            c['no max']+=1; continue
        sv=sum(v.get('val',0) for v in ents.values())
        smp=sum(v.get('max_pow',0) for v in ents.values())
        sprov=sum(v.get('province_power',0) for v in ents.values())
        gap=n['total']-sv
        d_max=n['max']-smp          # candidate: pirate max_pow
        d_pp=n['p_pow']-sprov        # candidate
        k=('gap0' if gap<0.0015 else 'gapPos', 'dmax0' if abs(d_max)<0.0015 else ('dmax=gap' if abs(d_max-gap)<0.0035 else 'dmax other'))
        c[k]+=1
        if k[1]=='dmax other' and len(ex)<8: ex.append((e['id'],n['definitions'],round(gap,3),round(d_max,3),round(d_pp,3)))
        stat['dmax_vs_gap'].append((gap,d_max))
print(c); print(ex)
# p_pow - sum province power distribution
