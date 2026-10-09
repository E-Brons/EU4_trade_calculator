"""R02: away collectors (has_trader, no `type`, not has_capital) among all countries across the series, and their max_demand vs the country's foreign-class value."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_c_lib as L
S=L.series()
for lab,ns in S:
    away=[];home=[]
    cls=collections.defaultdict(collections.Counter)
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and 'max_demand' in e: cls[k][e['max_demand']]+=1
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and e.get('has_trader') and 'type' not in e and 'money' in e:
                (home if e.get('has_capital') else away).append((n['definitions'],k,e['max_demand'],cls[k].most_common(1)[0][0]))
    ratio=[round(md/mode,3) for _,_,md,mode in away]
    print(lab,'collectors with merchant at home node:',len(home),'away:',len(away), collections.Counter(ratio).most_common(4))

print('=== exact test: away md == foreign-class mode / 2 (tolerance 0.0011)')
tot=ok=0; fails=[]
for lab,ns in S:
    cls=collections.defaultdict(collections.Counter)
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and 'max_demand' in e: cls[k][e['max_demand']]+=1
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and e.get('has_trader') and 'type' not in e and 'money' in e and not e.get('has_capital'):
                mode=cls[k].most_common(1)[0][0]
                tot+=1
                if abs(e['max_demand']-mode/2)<=0.0011: ok+=1
                else: fails.append((lab,k,n['definitions'],e['max_demand'],mode,dict(cls[k])))
print(tot,ok,len(fails)); 
for f in fails[:12]: print(f)

print('=== refined: base = domestic value if top_provinces[0]==tag else foreign-class mode (tolerance 0.0011)')
tot=ok=0; fails=[]; by=collections.Counter()
for lab,ns in S:
    cls=collections.defaultdict(collections.Counter); dom={}
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and 'max_demand' in e:
                cls[k][e['max_demand']]+=1
                if e.get('has_capital'): dom[k]=e['max_demand']
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and e.get('has_trader') and 'type' not in e and 'money' in e and not e.get('has_capital'):
                tp=L.as_list(n.get('top_provinces'))
                top = bool(tp) and tp[0]==k
                base = dom.get(k) if top else cls[k].most_common(1)[0][0]
                tot+=1; by[top]+=1
                if base is not None and abs(e['max_demand']-base/2)<=0.0011: ok+=1
                else: fails.append((lab,k,n['definitions'],e['max_demand'],base,top,dict(cls[k])))
print(tot,ok,len(fails),'top-province cases',by[True])
for f in fails[:12]: print(f)

print('=== steerers (type present) away from the capital node: md vs base (not halved)')
tot=full=half=other=0; ex=[]
for lab,ns in S:
    cls=collections.defaultdict(collections.Counter); dom={}
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and 'max_demand' in e:
                cls[k][e['max_demand']]+=1
                if e.get('has_capital'): dom[k]=e['max_demand']
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k) and e.get('has_trader') and 'type' in e and not e.get('has_capital'):
                tp=L.as_list(n.get('top_provinces')); top=bool(tp) and tp[0]==k
                base=dom.get(k) if top else cls[k].most_common(1)[0][0]
                if base is None: continue
                tot+=1; r=e['max_demand']/base
                if abs(r-1)<=0.002: full+=1
                elif abs(r-0.5)<=0.002: half+=1
                else:
                    other+=1; ex.append((lab,k,n['definitions'],e['max_demand'],base))
print(tot,'full',full,'half',half,'other',other, ex[:6])
pairs={(k,nd) for lab,ns in S for n in ns for k,e in n.items() if isinstance(e,dict) and L.TAGLIKE(k) and e.get('has_trader') and 'type' not in e and 'money' in e and not e.get('has_capital') for nd in [n['definitions']]}
print('distinct (country,node) away-collector pairs',len(pairs),'distinct countries',len({p[0] for p in pairs}))
print('distinct steerer exceptions:', sorted({(e[1],e[2]) for e in ex}))
