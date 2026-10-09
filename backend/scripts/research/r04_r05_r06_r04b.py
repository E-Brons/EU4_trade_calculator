import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
exec(open('/tmp/eu4research/repo/backend/scripts/research/r04_r05_r06_r05g.py').read().split("# candidate")[0])
PL=('S79','S80','U01','U02')
cands = set(idx)
for (sid,D,tag), r in idx.items():
    if r.get('province_power',0) >= 10:
        for B in g.nodes:
            if D in g.outgoing(B) and (sid,B) in nidx: cands.add((sid,B,tag))
# (a) receivers: entries with t_in>0 at a downstream node of B whose link is active, tag's pD>=10 there
recv_d = set((sid,D,tag) for (sid,D,tag),r in idx.items() if r.get('t_in',0)>0)
giv_d = set((sid,D,tag) for (sid,D,tag),r in idx.items() if r.get('t_out',0)>0)
def test(S, label):
    n=ok=0
    for (sid,B,tag) in cands:
        if sid in PL: continue
        sp = as_list(nidx[(sid,B)].get('steer_power'))
        for i,D in enumerate(g.outgoing(B)):
            if (sid,D,tag) in S and idx[(sid,D,tag)].get('province_power',0)>=10 and i<len(sp) and sp[i]>0:
                n+=1; ok += abs(pred(sid,B,tag)-idx.get((sid,B,tag),{}).get('prev',0.0))<1e-6; break
    print(label, 'entries', n, 'prev matches the province_power-only rule', ok)
test(recv_d,'receiver at downstream node (t_in>0)')
test(giv_d,'giver at downstream node (t_out>0)')
# giver prev included in val -> t_out
G=[r for r in idx.values() if r.get('t_out',0)>0]
print('givers with prev>0:', sum(1 for r in G if r.get('prev',0)>0), ' givers with val==max_pow*max_demand trunc3 and t_out from val:', sum(1 for r in G if abs(tr(r['max_pow']*r['max_demand'])-r['val'])<1e-9))
# receivers: max_pow has no t_in term: extras check for snapshots
R=[r for r in idx.values() if r.get('t_in',0)>0 and r['sid'] not in PL and 'max_pow' in r]
print('snapshot receivers with max_pow', len(R), ' max_pow == prov+ship+prev+capital*5+mods:', sum(1 for r in R if abs(r['max_pow']-(r.get('province_power',0)+r.get('ship_power',0)+r.get('prev',0)+5*bool(r.get('has_capital'))+sum(float(m.get('power',0)) for m in as_list(r.get('modifier')) if isinstance(m,dict))))<1e-6))
print('receiver examples (S42):', [(r['node'],r['tag'],r['max_pow'],r['t_in'],r['val']) for r in R if r['sid']=='S42'][:4])
