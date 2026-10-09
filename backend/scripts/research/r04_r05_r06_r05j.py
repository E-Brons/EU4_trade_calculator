import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
exec(open('/tmp/eu4research/repo/backend/scripts/research/r04_r05_r06_r05g.py').read().split("# candidate")[0])
PLAYED = ('S79','S80','U01','U02')
def link_state(sid,B,D):
    sp = as_list(nidx[(sid,B)].get('steer_power')); i = list(g.outgoing(B)).index(D)
    w = sp[i] if i < len(sp) else 0.0
    n = nidx[(sid,D)]; order=n['order']; incv=None; adds=None
    for x in as_list(n.get('incoming')):
        if isinstance(x, dict) and order[int(x['from'])-1]==B: incv = x['value']; adds = x.get('add')
    return w, incv, adds
# per link (B,D,tag) with pD>=10 and the *only* link of that tag (single) : propagated?
single=[]
for (sid,D,tag), r in idx.items():
    p = r.get('province_power',0)
    if p < 10: continue
    for B in g.nodes:
        if D in g.outgoing(B) and (sid,B) in nidx:
            ds = [d for d in g.outgoing(B) if idx.get((sid,d,tag),{}).get('province_power',0)>=10]
            if ds != [D]: continue
            rec = idx.get((sid,B,tag),{}).get('prev',0.0)
            single.append((sid,B,D,tag,p,rec>0, link_state(sid,B,D), nidx[(sid,B)].get('outgoing')))
for lab, S in (('snapshots',[s for s in single if s[0] not in PLAYED]),('played',[s for s in single if s[0] in PLAYED])):
    c = collections.Counter()
    for sid,B,D,tag,p,P,(w,incv,adds),outg in S:
        c[(P, 'w>0' if w>0 else 'w0', 'inc>0' if (incv or 0)>0 else ('inc0' if incv is not None else 'noinc'))]+=1
    print(lab, len(S)); [print('   ',k,v) for k,v in sorted(c.items(), key=str)]
