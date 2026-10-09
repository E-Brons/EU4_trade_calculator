"""Entries with downstream ship_power>0 (link with province_power>=10): does the ungated prev rule hold without any ship term? MOR in U03-U05? Run from backend/."""
import sys, collections
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common
from u345_pipe_prev import *
for e in common.entries() + NEW:
    if e['id'] not in ('S79', 'S80', 'U03', 'U04', 'U05'): continue
    ns = {n['definitions']: n for n in common.nodes(e)}
    T = {nid: tags(n) for nid, n in ns.items()}
    c = collections.Counter(); morw = []
    for B in ns:
        for tag in set(t for Dn in out.get(B, []) for t in T.get(Dn, {})):
            links = [(Dn, T[Dn][tag].get('province_power', 0.0), T[Dn][tag].get('ship_power', 0.0)) for Dn in out.get(B, []) if tag in T.get(Dn, {}) and T[Dn][tag].get('province_power', 0.0) >= 10]
            if not any(s > 0 for _, _, s in links): continue
            rec = T[B].get(tag, {}).get('prev', 0.0); ung = sum(d5(p) for _, p, _ in links)
            poly = (B == 'polynesia_node')
            c['ship entries'] += 1; c['ship entries excl polynesia_node'] += (not poly)
            c['ungated ok excl polynesia_node'] += (not poly) and abs(ung - rec) < 5e-4
            if tag == 'MOR': morw.append((B, rec, round(ung, 3), links))
    mor_ship = sum(1 for nid in ns if 'MOR' in T[nid] and T[nid]['MOR'].get('ship_power', 0) > 0)
    print(e['id'], dict(c), '| MOR entries with own ship_power>0:', mor_ship, '| MOR entries with downstream ships (pD>=10):', len(morw), morw[:3])
