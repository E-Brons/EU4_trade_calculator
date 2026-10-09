"""Ungated prev rule failures in the played saves: residual vs downstream ship_power, and MOR presence. Run from backend/."""
import sys, collections
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common
from common import as_list
from u345_pipe_prev import *

def ungated_fails(e):
    ns = {n['definitions']: n for n in common.nodes(e)}
    T = {nid: tags(n) for nid, n in ns.items()}
    cands = set()
    for nid, tg in T.items():
        for tag, c in tg.items():
            if ent(c): cands.add((nid, tag))
            if c.get('province_power', 0) >= 10:
                for (B, i) in inn[nid]:
                    if B in ns: cands.add((B, tag))
    res = []
    for (B, tag) in sorted(cands):
        rec = T[B].get(tag, {}).get('prev', 0.0)
        links = [(T[Dn][tag].get('province_power', 0.0), T[Dn][tag].get('ship_power', 0.0), Dn) for Dn in out.get(B, []) if tag in T.get(Dn, {}) and T[Dn][tag].get('province_power', 0.0) >= 10]
        ung = sum(d5(p) for p, s, _ in links)
        if abs(ung - rec) >= 0.0005:
            res.append((B, tag, rec, round(ung, 3), round(rec - ung, 3), [(Dn, p, s) for p, s, Dn in links]))
    return res, len(cands)
for e in common.entries() + NEW:
    if e['id'] in ('S79', 'S80', 'U03', 'U04', 'U05'):
        f, n = ungated_fails(e)
        print(e['id'], e['date'], 'candidates', n, 'ungated-rule fails', len(f))
        for x in f: print('   ', x)
