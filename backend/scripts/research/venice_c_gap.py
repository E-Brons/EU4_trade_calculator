"""R10: node total - sum(val) and the part not explained by uncredited province power (p_pow - sum province_power), all 24 Venice saves + S01."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_c_lib as L
S=L.series()
TOL=0.0035
for lab,ns in S:
    gaps=[];unexpl=[];nm=0
    for n in ns:
        if 'total' not in n: continue
        nm+=1
        ents=[e for k,e in n.items() if isinstance(e,dict) and L.TAGLIKE(k)]
        sv=sum(e.get('val',0) for e in ents if isinstance(e,dict))
        sp=sum(e.get('province_power',0) for e in ents)
        gap=n['total']-sv
        unc=(n.get('p_pow',sp)-sp)
        if abs(gap)>TOL: gaps.append((n['definitions'],round(gap,3),round(unc,3)))
        if abs(gap-unc)>TOL: unexpl.append((n['definitions'],round(gap,3),round(unc,3)))
    print(lab,'nodes with total',nm,'gap>tol',len(gaps),'gap != (p_pow - sum province_power)',len(unexpl),gaps[:3],unexpl[:3])
