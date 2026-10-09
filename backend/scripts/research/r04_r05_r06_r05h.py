import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
exec(open('/tmp/eu4research/repo/backend/scripts/research/r04_r05_r06_r05g.py').read().split("# candidate")[0])
snap = [k for k in idx if k[0] not in ('S79','S80','U01','U02')]
cands = set(k for k in idx if k[0] not in ('S79','S80','U01','U02'))
for (sid,D,tag), r in idx.items():
    if sid in ('S79','S80','U01','U02'): continue
    if r.get('province_power',0) >= 10:
        for B in g.nodes:
            if D in g.outgoing(B) and (sid,B) in nidx: cands.add((sid,B,tag))
def links(sid,B,tag):
    sp = as_list(nidx[(sid,B)].get('steer_power')); out=[]
    for i,D in enumerate(g.outgoing(B)):
        r = idx.get((sid,D,tag))
        if r and r.get('province_power',0)>=10 and i<len(sp) and sp[i]>0: out.append(r['province_power'])
    return out
V = {'exact sum/5': lambda ps: sum(ps)/5, 'trunc3(sum/5)': lambda ps: tr(sum(ps)/5), 'sum(trunc3(p/5))': lambda ps: sum(tr(p/5) for p in ps),
     'round3(sum/5)': lambda ps: math.floor(sum(ps)/5*1000+.5)/1000, 'sum(round3(p/5))': lambda ps: sum(math.floor(p/5*1000+.5)/1000 for p in ps)}
multi = [k for k in cands if len(links(*k))>=2]
single = [k for k in cands if len(links(*k))==1]
print('snapshot candidates', len(cands), 'single-link', len(single), 'multi-link', len(multi))
for name,fn in V.items():
    for lab, S in (('all',cands),('single',single),('multi',multi)):
        ok = sum(1 for k in S if abs(fn(links(*k)) - idx.get(k,{}).get('prev',0.0)) < 1e-6)
        print(f'{name:20s} {lab:7s} exact-match {ok}/{len(S)}')
# threshold neighbourhood among links with weight>0 (snapshots)
below = []; above = []
for (sid,D,tag), r in idx.items():
    if sid in ('S79','S80','U01','U02'): continue
    p = r.get('province_power',0)
    if 9 <= p < 10: below.append((p,sid,D,tag))
    if 10 <= p < 11: above.append((p,sid,D,tag))
print('max pD<10', max(below)[0] if below else None, ' min pD>=10', min(above)[0] if above else None)
# among single-link w>0 candidates with pD in [9,10): any propagated?
n_below_prop = 0; n_below = 0
for (sid,B,tag) in single: pass
cnt = collections.Counter()
for (sid,D,tag), r in idx.items():
    if sid in ('S79','S80','U01','U02'): continue
    p = r.get('province_power',0)
    if not (9.0 <= p < 12.0): continue
    for B in g.nodes:
        if D in g.outgoing(B) and (sid,B) in nidx:
            i = list(g.outgoing(B)).index(D); sp = as_list(nidx[(sid,B)].get('steer_power'))
            if i < len(sp) and sp[i] > 0:
                # B's prev from only this link?
                others = [x for x in links(sid,B,tag) if x != p]
                if others: continue
                rec = idx.get((sid,B,tag),{}).get('prev',0.0)
                cnt[(round(p,1)//1, rec>0)] += 1
print('pD bucket (floor) -> propagated?', sorted(cnt.items()))
# distinct values of pD just under and just over 10
vals = sorted(set(round(p,3) for p,*_ in below))[-6:], sorted(set(round(p,3) for p,*_ in above))[:6]
print(vals)
