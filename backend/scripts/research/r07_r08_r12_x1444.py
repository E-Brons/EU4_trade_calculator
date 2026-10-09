import sys, json, itertools; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_income import *
def collect(sid='S01', mintot=1.0):
    e=[x for x in common.entries() if x['id']==sid][0]
    C=common.block(e,'countries')
    out={}
    for ee,n,t,x in rows():
        if ee['id']!=sid or not x.get('has_capital'): continue
        tot=f(x['total'])
        if tot<mintot: continue
        lo,hi=xint(f(x['money']),tot); X=(lo+hi)/2
        c=C.get(t)
        if not isinstance(c,dict): continue
        out[t]=(X,c,x)
    return out
def feat(c,x):
    g=c.get('government') or {}
    rs=g.get('reform_stack',{}) if isinstance(g,dict) else {}
    reforms=tuple(sorted(r for r in common.as_list(rs.get('reforms')) if r not in('monarchy_mechanic','republic_mechanic')))
    return dict(religion=c.get('religion'), reforms=reforms, rank=c.get('government_rank'), gov=c.get('government_name'),
                merc=c.get('mercantilism'), has_trader=bool(x.get('has_trader')), culture=c.get('primary_culture'),
                tech=tuple((c.get('technology') or {}).values()), inst=tuple(common.as_list(c.get('institutions'))),
                ideas=tuple(sorted((c.get('active_idea_groups') or {}).items())) if isinstance(c.get('active_idea_groups'),dict) else None,
                nmerch=len(common.as_list((c.get('merchants') or {}).get('envoy'))) if isinstance(c.get('merchants'),dict) else None)
if __name__=='__main__':
    D=collect()
    print(len(D))
    names=['religion','reforms','rank','gov','merc','has_trader','tech','inst','ideas','nmerch']
    for r in range(1,3):
        for combo in itertools.combinations(names,r):
            groups=defaultdict(set)
            for t,(X,c,x) in D.items():
                F=feat(c,x); groups[tuple(F[k] for k in combo)].add(round(X,2))
            bad=sum(1 for v in groups.values() if len(v)>1)
            print(combo,'groups',len(groups),'inconsistent',bad)
