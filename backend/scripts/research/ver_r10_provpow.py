"""Verifier (independent): province_power of a (country,node) entry vs sum of trade_power of provinces it controls in the node."""
import sys, re, collections
sys.path.insert(0, 'scripts/research')
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
mag = collections.Counter(); tagc = collections.Counter(); C = collections.Counter(); bad = collections.Counter(); ex = []
for e in common.entries():
    ps = common.block(e, 'provinces'); ctl = collections.defaultdict(float); own = collections.defaultdict(float)
    for p in ps.values():
        if isinstance(p, dict) and 'trade' in p:
            ctl[(p['trade'], p.get('controller'))] += p.get('trade_power', 0.0)
    for n in common.nodes(e):
        nid = n['definitions']
        tags = [k for k, v in n.items() if TAG.match(k) and isinstance(v, dict)]
        for k in tags:
            if k == 'PIR': continue
            C['entries'] += 1
            pp = n[k].get('province_power', 0.0)
            ok = abs(pp - ctl.get((nid, k), 0.0)) <= 0.002
            C['match'] += ok
            if not ok:
                dd=abs(pp-ctl.get((nid,k),0.0)); mag['>0.002']+=1; mag['>0.01']+=dd>0.01; mag['>0.1']+=dd>0.1; mag['>0.5']+=dd>0.5
                bad[e['id']] += 1; tagc[(('col' if re.fullmatch(r'C\d\d', k) else 'other'), e['id'] in ('S79','S80','U01','U02'), round(pp-ctl.get((nid,k),0.0),0))] += 1
                if len(ex) < 6: ex.append((e['id'], nid, k, pp, round(ctl.get((nid, k), 0.0), 3)))
print(dict(C), 'mismatch', C['entries'] - C['match']); print(bad.most_common(8)); print(ex)
print(sorted(tagc.items(), key=lambda x:-x[1])[:14])
print(dict(mag))
