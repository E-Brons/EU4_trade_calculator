"""R06: extras = max_pow - province_power - ship_power - prev, grouped by entry class."""
import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, collections
rows, nodes = fl.load()
E = [r for r in rows if 'max_pow' in r]
def cls(r):
    if r.get('has_capital'): a='home'
    elif 'total' in r: a='collect-away'
    elif 'type' in r: a='steer'
    else: a='passive'
    return a + ('+merchant' if r.get('has_trader') else '')
def extras(r): return round(r['max_pow']-r.get('province_power',0)-r.get('ship_power',0)-r.get('prev',0),3)
tab = collections.defaultdict(collections.Counter)
for r in E: tab[cls(r)][extras(r)] += 1
print(len(E))
for c, cn in sorted(tab.items()):
    print(c, sum(cn.values()), cn.most_common(14))

print('=== residual after capital 5 and modifier powers')
from common import as_list
def mods(r):
    return [m for m in as_list(r.get('modifier')) if isinstance(m, dict)]
mk = collections.Counter(); 
for r in E:
    for m in mods(r): mk[(m.get('key'), m.get('power'), m.get('duration'))]+=1
print(mk.most_common(15))
res = collections.defaultdict(collections.Counter)
for r in E:
    x = extras(r) - (5.0 if r.get('has_capital') else 0.0) - sum(float(m.get('power',0)) for m in mods(r))
    res[cls(r)][round(x,3)] += 1
for c, cn in sorted(res.items()): print(c, sum(cn.values()), cn.most_common(10))

print('=== per-country consistency of residual (merchant entries)')
def resid(r): return round(extras(r) - (5.0 if r.get('has_capital') else 0.0) - sum(float(m.get('power',0)) for m in mods(r)),3)
M = [r for r in E if r.get('has_trader')]
by = collections.defaultdict(list)
for r in M: by[(r['sid'],r['tag'])].append((r['node'], cls(r), resid(r)))
nz = {k:v for k,v in by.items() if any(x[2] for x in v)}
print('country-saves with merchants', len(by), 'with nonzero residual somewhere', len(nz))
print(collections.Counter(k[1] for k in nz).most_common(25))
# example
for k in list(nz)[:6]: print(k, nz[k][:12])
# the tags that are nonzero in S14
print([ (k[1], sorted(set(x[2] for x in v))) for k,v in nz.items() if k[0]=='S14'])

print('=== played saves: residual by country')
PL = ('S79','S80','U01','U02')
print('nonzero residual outside played saves:', sum(1 for r in E if r['sid'] not in PL and resid(r)!=0))
cons = collections.Counter(); mixed=[]
for (sid,tag),v in by.items():
    if sid not in PL: continue
    vals = sorted(set(x[2] for x in v))
    cons[tuple(vals)] += 1
    if len(vals)>1: mixed.append((sid,tag,[(n,c,x) for n,c,x in v if True][:14]))
print(cons.most_common(12))
for m in mixed[:8]: print(m)
# same tag in S80 vs S79 (different years)?
for tag in ('MIR','KON','C03','TUR','MOR','POR'):
    print(tag, {sid: sorted(set(x[2] for x in by.get((sid,tag),[]))) for sid in PL})

print('=== residual vs country features (S80)')
import common
ent = {e['id']: e for e in common.entries()}
C = common.block(ent['S80'],'countries')
rows2=[]
for (sid,tag),v in by.items():
    if sid!='S80': continue
    c=C.get(tag,{})
    ideas = c.get('active_idea_groups') or {}
    rows2.append((sorted(set(x[2] for x in v)), tag, ideas, c.get('estate'), c.get('government_name')))
cross = collections.defaultdict(collections.Counter)
for res,tag,ideas,est,gov in rows2:
    r=res[0] if len(res)==1 else tuple(res)
    cross[r]['trade_ideas=%s'%ideas.get('trade_ideas')]+=1
for r,cn in cross.items(): print(r, dict(cn))
print([ (r[0],t) for r in rows2 for t in [r[1]] if r[0]==[7.0]][:12])
print('VER', [x for x in by[('S80','VER')]])

print('=== +5 feature search (S80)')
def has5(res): return any(x in (7.0,22.0) for x in res)
grp = {tag:(has5(res)) for res,tag,ideas,est,gov in rows2 if len(res)==1}
tags5 = [t for t,v in grp.items() if v]; tags0=[t for t,v in grp.items() if not v]
print(len(tags5), len(tags0))
import json
c=C['HAB']; print(json.dumps(c.get('estate'),default=str)[:600])
print(c.get('government'))
def feat(tag):
    c=C[tag]; f={}
    gov=c.get('government')
    f['gov']=gov.get('reform_stack',{}) if isinstance(gov,dict) else None
    return c

print('=== feature separation for +5 (and +15 vs trade_ideas)')
def features(c):
    f=set()
    gov=c.get('government')
    if isinstance(gov,dict):
        for r in gov.get('reform_stack',{}).get('reforms',[]) or []: f.add('reform:'+str(r))
        f.add('govtype:'+str(gov.get('government')))
    for e in as_list(c.get('estate')):
        if isinstance(e,dict):
            for p in e.get('granted_privileges',[]) or []:
                if isinstance(p,list) and p: f.add('priv:'+str(p[0]))
    for m in as_list(c.get('modifier')):
        if isinstance(m,dict): f.add('mod:'+str(m.get('modifier')))
    for k,v in (c.get('active_idea_groups') or {}).items(): f.add('idea:%s>=%s'%(k,v)); 
    f.add('tg:'+str(c.get('technology_group'))); f.add('rel:'+str(c.get('religion')))
    return f
for sidx in ('S80','S79'):
    Cc = common.block(ent[sidx],'countries')
    g5 = {}
    for (sid,tag),v in by.items():
        if sid!=sidx: continue
        vals=set(x[2] for x in v)
        if len(vals)==1: g5[tag]=next(iter(vals)) in (7.0,22.0)
    pos=[t for t,v in g5.items() if v]; neg=[t for t,v in g5.items() if not v]
    cnt=collections.Counter(); 
    F={t:features(Cc[t]) for t in g5}
    allf=set().union(*F.values())
    sc=[]
    for f in allf:
        tp=sum(1 for t in pos if f in F[t]); fp=sum(1 for t in neg if f in F[t])
        sc.append((tp-fp*3, tp, fp, f))
    sc.sort(reverse=True)
    print(sidx, 'pos', len(pos), 'neg', len(neg)); [print('  ',x) for x in sc[:8]]

print('=== rule check')
REF = {'reform:mercantilistic_approach_reform','reform:pious_merchants_reform'}
for sidx in ('S79','S80'):
    Cc = common.block(ent[sidx],'countries'); tot=collections.Counter(); bad=[]
    for (sid,tag),v in by.items():
        if sid!=sidx: continue
        vals=sorted(set(x[2] for x in v)); f=features(Cc[tag]); ideas=Cc[tag].get('active_idea_groups') or {}
        five = bool(f & REF); fifteen = (ideas.get('trade_ideas') or 0) >= 5
        pred = 2 + 5*five + 15*fifteen
        ok = vals==[pred]
        tot[ok]+=1
        if not ok: bad.append((tag, vals, pred, five, ideas.get('trade_ideas'), sorted(x for x in f if x.startswith('reform:'))[:0]))
    print(sidx, dict(tot)); [print('  ',b) for b in bad[:12]]

print('=== snapshots: would the played-save rule predict >0?')
n=collections.Counter()
for sidx in ('S42','S67','S78','S14'):
    Cc = common.block(ent[sidx],'countries')
    for (sid,tag),v in by.items():
        if sid!=sidx: continue
        f=features(Cc[tag]); ideas=Cc[tag].get('active_idea_groups') or {}
        pred = 2 + 5*bool(f&REF) + 15*((ideas.get('trade_ideas') or 0)>=5)
        n[(sidx, 'rule_pred>0', pred, 'observed', tuple(sorted(set(x[2] for x in v))))]+=1
for k,v in sorted(n.items(), key=str)[:14]: print(k,v)
print('snapshot countries with trade_ideas>=5 and merchants:', sum(c for k,c in n.items() if k[2]>=17))
# base '2' in snapshot: date of save on 1st?

print('=== played saves class table and oddities')
t2=collections.defaultdict(collections.Counter)
for r in E:
    if r['sid'] in PL: t2[cls(r)][resid(r)]+=1
for c,cn in sorted(t2.items()): print(c, dict(cn))
odd=[r for r in E if r['sid'] in PL and not r.get('has_trader') and resid(r)!=0]
for r in odd[:6]: print(r['sid'],r['node'],r['tag'],cls(r),resid(r),{k:r.get(k) for k in ('province_power','ship_power','prev','max_pow','modifier')})
# mod keys full table by class
mk2=collections.defaultdict(collections.Counter)
for r in E:
    for m in mods(r): mk2[(m.get('key'),m.get('power'))][cls(r)]+=1
for k,v in sorted(mk2.items(), key=lambda kv:-sum(kv[1].values()))[:14]: print(k, dict(v))
# recalled: has_trader flag
rc=collections.Counter()
for r in E:
    if any(m.get('key')=='merchant_recalled' for m in mods(r)): rc[(cls(r), r['sid'] in PL, resid(r))]+=1
print('recalled', dict(rc))

print('=== full decomposition check in played saves')
CC = {s: common.block(ent[s],'countries') for s in ('S79','S80','U01','U02')}
res_c = collections.Counter(); exc = collections.Counter()
for r in E:
    if r['sid'] not in CC: continue
    c = CC[r['sid']].get(r['tag'],{}); f = features(c); ideas=c.get('active_idea_groups') or {}
    R = 2 + 5*bool(f&REF) + 15*((ideas.get('trade_ideas') or 0)>=5)
    merchant = bool(r.get('has_trader'))
    pred = 5.0*bool(r.get('has_capital')) + sum(float(m.get('power',0)) for m in mods(r)) + (R if merchant else 0.0)
    ok = abs(pred-extras(r))<1e-6
    res_c[ok]+=1
    if not ok: exc[(r['sid'],r['tag'],r['node'],cls(r),extras(r),round(pred,3))]+=1
print(dict(res_c)); 
for k in list(exc)[:20]: print(k)
# recalled powers and durations
rp=collections.Counter(); 
for r in E:
    for m in mods(r):
        if m.get('key')=='merchant_recalled': rp[m.get('power')]+=1
print('recalled powers', rp)
d=[m.get('duration') for r in E for m in mods(r) if m.get('key')=='merchant_recalled']; print(min(d),max(d),len(d))
