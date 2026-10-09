"""What distinguishes nodes where the weight gate fails (played saves) from where it holds? Run from backend/."""
import sys, collections
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common
from common import as_list
from u345_pipe_prev import *

def analyse(e, show=True):
    ns = {n['definitions']: n for n in common.nodes(e)}
    T = {nid: tags(n) for nid, n in ns.items()}
    bad_nodes = collections.Counter(); good_nodes = collections.Counter()
    info = {}
    for nid, n in ns.items():
        sp = as_list(n.get('steer_power')); info[nid] = sp
    for nid, tg in T.items():
        for tag, c in tg.items():
            if c.get('province_power', 0) < 10: continue
            for (B, i) in inn[nid]:
                if B not in ns: continue
                sp = info[B]; w = sp[i] if i < len(sp) else None
                rec = T[B].get(tag, {}).get('prev', 0.0)
                # contribution of this single link only matters if alone; use all links of (B,tag)
    # per (B,tag) classify: ungated ok?, gated ok?
    cls = collections.Counter(); ex = collections.defaultdict(list)
    for B in ns:
        sp = info[B]
        for tag in set(t for Dn in out.get(B, []) for t in T.get(Dn, {})):
            links = [(i, Dn, T[Dn][tag].get('province_power', 0.0)) for i, Dn in enumerate(out[B]) if tag in T.get(Dn, {}) and T[Dn][tag].get('province_power', 0.0) >= 10]
            if not links: continue
            rec = T[B].get(tag, {}).get('prev', 0.0)
            ung = sum(d5(p) for _, _, p in links); gat = sum(d5(p) for i, _, p in links if i < len(sp) and sp[i] > 0)
            k = ('ungated ok' if abs(ung - rec) < 5e-4 else 'ungated FAIL', 'gated ok' if abs(gat - rec) < 5e-4 else 'gated FAIL',
                 'node has >=1 positive weight' if any(x > 0 for x in sp) else 'node ALL weights 0/none')
            cls[k] += 1
            if len(ex[k]) < 3: ex[k].append((B, tag, sp, rec, round(ung, 3), round(gat, 3)))
    return cls, ex
for e in common.entries() + NEW:
    if e['id'] in ('S14', 'S79', 'S80', 'U03', 'U04', 'U05'):
        cls, ex = analyse(e)
        print(e['id'], e['date'])
        for k, v in sorted(cls.items(), key=lambda kv: -kv[1]): print('   ', v, k, ex[k][:2])
