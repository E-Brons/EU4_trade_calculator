"""Solve VEN's effective contribution X to the link weights at alexandria/ragusa/wien, assuming the others count with plain val."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V
import venice_b_8_weights as W
from venice_load import as_list

def nlinks(ns):
    names = [n['definitions'] for n in ns]; nl = collections.Counter()
    for n in ns:
        for inc in as_list(n.get('incoming')):
            if isinstance(inc, dict) and 'from' in inc: nl[names[int(inc['from']) - 1]] += 1
    return nl

for p in V.files():
    tag = p.stem[6:]
    if tag not in ('1444_12_01', '1445_03_01', '1445_03_31', '1445_04_01', '1445_05_01', '1445_06_01', '1445_07_02'): continue
    ns = V.nodes(p); nl = nlinks(ns)
    for n in ns:
        nm = n['definitions']
        if nm not in ('alexandria', 'ragusa', 'wien'): continue
        k = nl[nm]; w = n['steer_power']
        g = W.steerers(n, k)
        S = [sum(e.get('val', 0) for c, e in g.get(l, []) if c != 'VEN') for l in range(k)]
        v = n.get('VEN', {}); active = bool(v.get('type'))
        vl = int(v.get('steer_power', 0))
        T = sum(S); pr0 = [round(x / T, 3) for x in S]
        line = f"{tag} {nm:10s} w={w} plain(others)={pr0} VENactive={active} VENlink={vl} VENval={v.get('val')} maxpow={v.get('max_pow')} ship={v.get('ship_power')}"
        if active:
            # solve X from the weight of VEN's link:  (S_l + X)/(T+X) = w_l
            wl = w[vl]; X = (wl * T - S[vl]) / (1 - wl)
            line += f"  X={X:.2f}  X/val={X / v['val']:.3f}  X-val={X - v['val']:.2f}"
        print(line)
