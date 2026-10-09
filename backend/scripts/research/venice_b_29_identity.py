"""R08 C-06 identity 2 on the Venice saves (link order from the game's trade graph): incoming.add = outgoing * w_L * sum(add of entries with an `add` key on link L); all `add` entries vs only entries with `type`."""
import sys, collections
sys.path.insert(0, 'scripts/research'); sys.path.insert(0, '.')
import venice_load as V
from venice_load import as_list
from app.parsing.tradenodes import load_trade_graph
G = load_trade_graph()

def run(tag):
    p = [x for x in V.files() if x.stem.endswith(tag)][0]
    ns = V.nodes(p); names = [n['definitions'] for n in ns]; byn = dict(zip(names, ns))
    res = collections.Counter()
    for n in ns:
        nm = n['definitions']; w = n.get('steer_power'); outs = G.nodes[nm].outgoing
        if not outs or not isinstance(w, list) or len(w) != len(outs) or not n.get('outgoing'): continue
        for l, dst in enumerate(outs):
            d = byn[dst]; frm = names.index(nm) + 1
            inc = [x for x in as_list(d.get('incoming')) if isinstance(x, dict) and x.get('from') == frm]
            if not inc: continue
            inc = inc[0]
            s_all = sum(e.get('add', 0) for c, e in n.items() if isinstance(e, dict) and c.isupper() and 'add' in e and int(e.get('steer_power', 0)) == l)
            s_typ = sum(e.get('add', 0) for c, e in n.items() if isinstance(e, dict) and c.isupper() and e.get('type') and 'add' in e and int(e.get('steer_power', 0)) == l)
            tol = 0.0015 + n['outgoing'] * 0.001 * (1 + 0.06 * 20)
            for key, s in (('all_add', s_all), ('type_only', s_typ)):
                res[(key, abs(inc['add'] - n['outgoing'] * w[l] * s) <= tol)] += 1
    return dict(sorted(res.items()))
for t in sys.argv[1:]: print(t, run(t))
