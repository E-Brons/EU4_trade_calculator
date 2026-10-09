"""R05 summary numbers cited in the response (run: python scripts/research/r04_r05_r06_r05_summary.py)."""
import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
exec(open('/tmp/eu4research/repo/backend/scripts/research/r04_r05_r06_r05g.py').read().split("for use_w in")[0])
PLAYED = ('S79','S80','U01','U02')
def ok(k, **kw): return abs(pred(*k, **kw) - idx.get(k,{}).get('prev',0.0)) < 1e-6
for lab, S in (('snapshots S01-S78', [k for k in cands if k[0] not in PLAYED]), ('played S79,S80,U01,U02', [k for k in cands if k[0] in PLAYED])):
    print(lab, 'candidates', len(S))
    print('   threshold 10 + trunc per link, no weight gate :', sum(ok(k,use_w=False) for k in S))
    print('   + weight gate                                 :', sum(ok(k) for k in S))
    if lab.startswith('played'):
        print('   + weight gate + MOR ship term 0.25            :', sum(abs(pred(*k, ships=(0.25 if k[2]=='MOR' else 0.0)) - idx.get(k,{}).get('prev',0.0)) < 1e-6 for k in S))
        print('   gate only for non-gated explanation: no-weight rule or MOR ship term explains', sum((ok(k) or ok(k,use_w=False) or (k[2]=='MOR' and abs(pred(*k,ships=0.25)-idx.get(k,{}).get('prev',0.0))<1e-6)) for k in S))
# links with weight 0 despite pD>=10: how many in snapshots, and prev always 0?
n=z=0
for (sid,D,tag), r in idx.items():
    if sid in PLAYED or r.get('province_power',0) < 10: continue
    for B in g.nodes:
        if D in g.outgoing(B) and (sid,B) in nidx:
            i = list(g.outgoing(B)).index(D); sp = as_list(nidx[(sid,B)].get('steer_power'))
            w = sp[i] if i < len(sp) else None
            if not (w and w>0): n += 1
print('snapshot (B,D,tag) links with pD>=10 and weight 0 (no propagation expected):', n)
# played saves: entries with downstream ship power, non-MOR
for sid in ('S79','S80','U01','U02'):
    ent = [k for k in cands if k[0]==sid and k[2]!='MOR' and any(idx.get((sid,D,k[2]),{}).get('ship_power',0)>0 for D in g.outgoing(k[1]))]
    print(sid, 'non-MOR entries with downstream ship_power>0:', len(ent), ' explained without ship term (no-weight or gated):', sum(ok(k) or ok(k,use_w=False) for k in ent))
