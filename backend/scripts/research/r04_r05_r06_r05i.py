import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
exec(open('/tmp/eu4research/repo/backend/scripts/research/r04_r05_r06_r05g.py').read().split("for use_w in")[0])
PLAYED = ('S79','S80','U01','U02')
bad = [k for k in cands if k[0] in PLAYED and abs(pred(*k,use_w=False)-idx.get(k,{}).get('prev',0.0))>=1e-6]
print(len(bad))
for k in sorted(bad):
    sid,B,tag = k
    print(k, 'rec', idx.get(k,{}).get('prev',0.0), 'pred_nw', round(pred(*k,use_w=False),3), 'downstream', [(D, idx.get((sid,D,tag),{}).get('province_power'), idx.get((sid,D,tag),{}).get('ship_power')) for D in g.outgoing(B)])
# in played saves: links with pD>=10 and weight 0: how many propagate?
n=p=0
for (sid,D,tag), r in idx.items():
    if sid not in PLAYED or r.get('province_power',0) < 10: continue
    for B in g.nodes:
        if D in g.outgoing(B) and (sid,B) in nidx:
            i = list(g.outgoing(B)).index(D); sp = as_list(nidx[(sid,B)].get('steer_power'))
            w = sp[i] if i < len(sp) else None
            if not (w and w>0):
                n += 1
                others = [x for x in links(sid,B,tag)] if False else []
print('played links pD>=10 weight 0:', n)
