"""Second pass (regex readers): cross-section of foreign-domestic vs DIP in U07; home bonus population rule; embargo rows U30; distinct away pairs."""
import sys, re, collections
sys.path.insert(0,'scripts/research')
import venice_c_raw as R
import venice_load as V
F=[p.name for p in V.files()]
# 1. cross-section U07
t=R.read(F[0]); e,_=R.trade_entries(t)
byc=collections.defaultdict(collections.Counter)
for (nd,tg),v in e.items():
    if 'max_demand' in v and tg!='PIR': byc[tg][v['max_demand']]+=1
two=ok=noruler=0
for tg,c in byc.items():
    if len(c)!=2: continue
    dip=R.ruler_dip(R.country_segment(t,tg))
    if dip is None: noruler+=1; continue
    two+=1
    f=c.most_common(1)[0][0]; d=min(c)
    if abs((f-d)-(0.012+0.005*dip))<1e-9: ok+=1
print(f'1. U07 two-class countries with a ruler: {two}, foreign-domestic == 0.012+0.005*DIP: {ok}; no ruler found: {noruler}')
# 2. home bonus population
res=collections.Counter(); ven=[]
for n in F[1:]:
    t=R.read(n); e,_=R.trade_entries(t)
    steer=collections.Counter(tg for (nd,tg),v in e.items() if v.get('has_trader') and 'type' in v)
    for tg in {tg for (_,tg) in e if tg!='PIR'}:
        if steer[tg]==0: continue
        seg=R.country_segment(t,tg)
        b=R.scalar(seg,'transfer_home_bonus')
        if b is None: continue
        res[abs(b-0.1*steer[tg])<1e-6]+=1
print('2. countries with >=1 steering merchant, field == 0.1 x steerers:',dict(res))
# 3. embargo rows U30
t=R.read(F[-1]); e,nodes=R.trade_entries(t)
def own(v): return v.get('max_pow',0)-v.get('prev',0) if 'max_pow' in v else 0.0
rows=[]
for x,by in (('ENG',['FRA']),('GEN',['LAN']),('LAN',['GEN'])):
    xs=[(nd,v) for (nd,tg),v in e.items() if tg==x and 'max_demand' in v]
    cnt=collections.Counter()
    bynode=collections.defaultdict(list)
    for (nd,tg),v in e.items(): bynode[nd].append((tg,v))
    for nd,v in xs:
        if sum(own(dict(bynode[nd])[b]) for b in by if b in dict(bynode[nd]))<=0 and not v.get('has_capital'): cnt[v['max_demand']]+=1
    cap=cnt.most_common(1)[0][0]
    for nd,v in xs:
        d=dict(bynode[nd]); eo=sum(own(d[b]) for b in by if b in d)
        if eo>0 and not v.get('has_capital'):
            tot=sum(own(w) for w in d.values())+5*sum(1 for w in d.values() if w.get('has_capital'))
            rows.append((x,nd,v['max_demand'],cap,round((1-v['max_demand']/cap)*100,2),round(50*eo/tot,2)))
print('3. U30 embargo rows (country,node,md,cap,obs%,pred%):'); [print('   ',r) for r in rows]
# 4. distinct away pairs
pairs=set()
for n in F:
    e,_=R.trade_entries(R.read(n))
    for (nd,tg),v in e.items():
        if v.get('has_trader') and 'type' not in v and 'money' in v and not v.get('has_capital'): pairs.add((tg,nd))
print('4. distinct (country,node) away-collector pairs:',len(pairs),'countries:',len({p[0] for p in pairs}))
