"""Alternative gate: link B->D counts for prev iff D's `incoming` list has an entry from B (presence / value>0). Compare with the weight gate. Run from backend/."""
import sys, collections
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common
from common import as_list
from u345_pipe_prev import *

def run(e):
    nl = common.nodes(e); order = [n['definitions'] for n in nl]
    ns = {n['definitions']: n for n in nl}
    T = {nid: tags(n) for nid, n in ns.items()}
    inc = {}   # (B,D) -> value sum
    for D_, n in ns.items():
        for i in as_list(n.get('incoming')):
            if isinstance(i, dict):
                fr = int(i['from']); B = order[fr - 1] if 0 < fr <= len(order) else None
                inc[(B, D_)] = inc.get((B, D_), 0.0) + float(i.get('value', 0.0))
    cnt = collections.Counter(); ex = collections.defaultdict(list)
    for B in ns:
        sp = as_list(ns[B].get('steer_power'))
        for tag in set(t for Dn in out.get(B, []) for t in T.get(Dn, {})) | set(t for t, c in T[B].items() if ent(c)):
            links = [(i, Dn, T[Dn][tag].get('province_power', 0.0)) for i, Dn in enumerate(out.get(B, [])) if tag in T.get(Dn, {}) and T[Dn][tag].get('province_power', 0.0) >= 10]
            rec = T[B].get(tag, {}).get('prev', 0.0)
            gates = {
              'weight>0': sum(d5(p) for i, Dn, p in links if i < len(sp) and sp[i] > 0),
              'incoming present': sum(d5(p) for i, Dn, p in links if (B, Dn) in inc),
              'incoming value>0': sum(d5(p) for i, Dn, p in links if inc.get((B, Dn), 0) > 0),
              'none': sum(d5(p) for i, Dn, p in links),
            }
            if not links and rec == 0: continue
            cnt['n'] += 1
            for g, v in gates.items():
                ok = abs(v - rec) < 5e-4; cnt[g] += ok
                if not ok and len(ex[g]) < 4: ex[g].append((B, tag, rec, round(v, 3), sp))
    return cnt, ex
import json
for e in common.entries() + NEW:
    if e['id'] in ('S14', 'S42', 'S79', 'S80', 'U03', 'U04', 'U05'):
        c, ex = run(e)
        print(e['id'], e['date'], dict(c))
        for g in ('incoming present', 'incoming value>0'): print('    first fails', g, ex[g][:3])
