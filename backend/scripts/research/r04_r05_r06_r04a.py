"""R04: transfers. givers = entries with t_out; receivers = entries with t_in."""
import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, collections, math
from common import as_list
rows, nodes = fl.load()
E = [r for r in rows if set(r)-{'max_demand','sid','node','tag','date'}]
tr = lambda x: math.trunc(x*1000+1e-9)/1000
G = [r for r in E if r.get('t_out',0) > 0]
R = [r for r in E if r.get('t_in',0) > 0]
print('entries', len(E), 'givers', len(G), 'receivers', len(R))
print('giver keys', collections.Counter(k for r in G for k in r).most_common(30))
d = [round(r['val']-2*r['t_out'],4) for r in G]
print('val-2*t_out: min', min(d), 'max', max(d), collections.Counter(d).most_common(5))
print('exact t_out = trunc3(0.5*(val-0.1))', sum(1 for r in G if abs(tr(0.5*(r['val']-0.1))-r['t_out'])<1e-9), 'of', len(G))
alts = {'trunc3(0.5*val)-0.05': lambda v: tr(0.5*v)-0.05, 'trunc3(0.5*val-0.05)': lambda v: tr(0.5*v-0.05), 'round3(0.5*(val-0.1))': lambda v: math.floor(0.5*(v-0.1)*1000+0.5)/1000,
        'trunc3(0.5*val)': lambda v: tr(0.5*v), 'trunc3(0.5*(val-0.1))': lambda v: tr(0.5*(v-0.1)), 'trunc3((val-0.1)/2) with val 0.101': lambda v: tr((v-0.101)/2)}
for n,f in alts.items(): print(n, sum(1 for r in G if abs(f(r['val'])-r['t_out'])<1e-9))
print('dependence on size: val quantiles', sorted(r['val'] for r in G)[::len(G)//8])
print('offset by val bucket', collections.Counter((round(math.log10(max(r['val'],1e-3))), round(r['val']-2*r['t_out'],3)) for r in G).most_common(12))
print('by save count', collections.Counter(r['sid'] for r in G).most_common(3), 'distinct tags', len(set(r['tag'] for r in G)))
print('min val of giver', min(r['val'] for r in G), 'min t_out', min(r['t_out'] for r in G))
print('givers with val<0.1?', sum(1 for r in G if r['val']<0.1))

print('=== giver kinds')
import common
ent={e['id']:e for e in common.entries()}
cb={}
giv=collections.Counter(); nong=collections.Counter(); ex=collections.defaultdict(set)
seen_g=set((r['sid'],r['tag']) for r in G)
for sid in ('S14','S42','S80','S79','S78'):
    cb[sid]=common.block(ent[sid],'countries')
    tagsE=set(r['tag'] for r in E if r['sid']==sid)
    for tag in tagsE:
        c=cb[sid].get(tag,{})
        if c.get('overlord'):
            kind='colonial' if c.get('colonial_parent') else 'other-subject'
            giv[(sid, kind, (sid,tag) in seen_g)]+=1
            if (sid,tag) not in seen_g: ex[(sid,kind)].add(tag)
print(sorted(giv.items()))
print({k:sorted(v)[:12] for k,v in ex.items()})

print('=== odd subjects')
for sid in ('S79','S80'):
    tagsE=set(r['tag'] for r in E if r['sid']==sid)
    for tag in sorted(tagsE):
        c=cb[sid].get(tag,{})
        if c.get('overlord') and ((sid,tag) in seen_g) != bool(c.get('colonial_parent')):
            print(sid, tag, 'overlord', c.get('overlord'), 'colonial_parent', c.get('colonial_parent'), 'giver', (sid,tag) in seen_g,
                  [ (r['node'], r.get('val'), r.get('t_out')) for r in E if r['sid']==sid and r['tag']==tag and (r.get('val') or r.get('t_out'))][:4])
# subjects in played saves: what distinguishes colonial? print keys with 'subject'
c=cb['S80']['C03']; print({k:c[k] for k in c if 'subject' in k})
print('vassal sample', {k:v for k,v in cb['S80']['BLG'].items() if 'subject' in k or k in ('overlord',)})

print('=== subject_focus vs giving (played S80 + S79 + S42)')
tab=collections.Counter()
for sid in ('S79','S80','S42','S78','S14'):
    tagsE=set(r['tag'] for r in E if r['sid']==sid)
    for tag in tagsE:
        c=cb[sid].get(tag,{})
        if c.get('overlord'):
            tab[(c.get('subject_focus'), 'colonial' if c.get('colonial_parent') else 'noncol', (sid,tag) in seen_g)]+=1
for k,v in sorted(tab.items(), key=str): print(k,v)
# any other key that differs between SND and the non-giving TUR subjects in S80
snd=cb['S80']['SND']; 
others=[cb['S80'][t] for t in ('BEI','BLG','HSK','HUN','IRQ','KLP','LUN','MHX','PTE','SIE','TMB','TTL') if t in cb['S80']]
for k in snd:
    if isinstance(snd[k],(int,float,str,bool)) and all(o.get(k)!=snd[k] for o in others) and k in ('subject_focus','subject_type','liberty_desire','tribute_type') : print(k, snd[k], [o.get(k) for o in others])
print({k:snd[k] for k in snd if 'lib' in k or 'focus' in k or 'tribut' in k or 'subject' in k})

print('=== transfer keys in country blocks')
tk=collections.Counter(); withk=collections.defaultdict(list)
for sid in ('S80','S79','S42','S14'):
    if sid not in cb: cb[sid]=common.block(ent[sid],'countries')
    for tag,c in cb[sid].items():
        if not isinstance(c,dict): continue
        for k in c:
            if 'transfer' in k: tk[(sid,k)]+=1; withk[(sid,k)].append((tag,c[k]))
print(tk)
for k,v in withk.items():
    if k[0] in ('S80',): print(k, v[:8])

print('=== flag vs t_out, all saves')
tab=collections.Counter(); odd=[]
for e in common.entries():
    sid=e['id']
    if sid not in cb: cb[sid]=common.block(e,'countries')
    tagsE=collections.defaultdict(list)
    for r in E:
        if r['sid']==sid: tagsE[r['tag']].append(r)
    for tag,rs in tagsE.items():
        c=cb[sid].get(tag,{})
        flag=bool(c.get('transfer_trade_power_to'))
        giv=any(r.get('t_out',0)>0 for r in rs)
        tab[(flag,giv)]+=1
        if flag and not giv: odd.append((sid,tag,c.get('transfer_trade_power_to'), [(r['node'],r.get('val'),r.get('has_trader')) for r in rs][:3], len(rs)))
    # countries with flag but no entries at all
    for tag,c in cb[sid].items():
        if isinstance(c,dict) and c.get('transfer_trade_power_to') and tag not in tagsE: tab[('flag,no entries',)]+=1
print(dict(tab))
print(odd[:10])
