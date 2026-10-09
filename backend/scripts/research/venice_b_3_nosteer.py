"""R08 Q5 on the Venice series: weights of nodes with >=2 links and no steering entry; test pull-direction models."""
import sys, itertools
sys.path.insert(0, 'scripts/research')
import venice_load as V
from venice_load import as_list

def graph(ns):
    names = [n['definitions'] for n in ns]
    out = {n: [] for n in names}
    for i, n in enumerate(ns):
        for inc in as_list(n.get('incoming')):
            if isinstance(inc, dict) and 'from' in inc:
                out[names[int(inc['from']) - 1]].append(names[i])
    return names, out

def reach(out, start):
    seen = set(); st = [start]
    while st:
        x = st.pop()
        for y in out[x]:
            if y not in seen:
                seen.add(y); st.append(y)
    return seen

def countries_in(n):
    return {k: v for k, v in n.items() if isinstance(v, dict) and k.isupper() and len(k) <= 3 and any(x in v for x in ('val', 'max_pow'))}

def analyse(tag, verbose=False):
    p = [x for x in V.files() if x.stem.endswith(tag)][0]
    ns = V.nodes(p); names, out = graph(ns); by = dict(zip(names, ns))
    collect = {}
    for n in ns:
        for c, e in countries_in(n).items():
            if 'money' in e or (e.get('has_trader') and 'type' not in e):
                collect.setdefault(c, set()).add(n['definitions'])
    rc = {nm: reach(out, nm) for nm in names}
    res = {}
    nodes = 0
    for nm in names:
        n = by[nm]; links = out[nm]
        w = n.get('steer_power')
        if len(links) < 2 or not isinstance(w, list) or (n.get('outgoing') or 0) <= 0:
            continue
        ents = countries_in(n)
        if any('add' in e or e.get('type') for e in ents.values()):
            continue
        if any('steer_power' in e for e in ents.values()):
            continue
        nodes += 1
        for model in MODELS:
            pred = model(nm, n, ents, links, rc, collect, by)
            if pred is None:
                continue
            res.setdefault(model.__name__, []).append(max(abs(a - b) for a, b in zip(pred, w)) < 0.0025)
    return nodes, {k: (sum(v), len(v)) for k, v in res.items()}

def norm(xs):
    s = sum(xs)
    return [x / s for x in xs] if s > 0 else None

def m_val_collect(nm, n, ents, links, rc, collect, by):
    xs = []
    for l in links:
        tgt = {l} | rc[l]
        xs.append(sum(e.get('val', 0) for c, e in ents.items() if collect.get(c, set()) & tgt and nm not in collect.get(c, set())))
    return norm(xs)

def m_maxpow_collect(nm, n, ents, links, rc, collect, by):
    xs = []
    for l in links:
        tgt = {l} | rc[l]
        xs.append(sum(e.get('max_pow', 0) for c, e in ents.items() if collect.get(c, set()) & tgt and nm not in collect.get(c, set())))
    return norm(xs)

def m_val_all_collect(nm, n, ents, links, rc, collect, by):
    xs = []
    for l in links:
        tgt = {l} | rc[l]
        xs.append(sum(e.get('val', 0) for c, e in ents.items() if collect.get(c, set()) & tgt))
    return norm(xs)

def m_total_down(nm, n, ents, links, rc, collect, by):
    return norm([by[l].get('total') or 0 for l in links])

def m_equal(nm, n, ents, links, rc, collect, by):
    return [1 / len(links)] * len(links)

MODELS = [m_val_collect, m_maxpow_collect, m_val_all_collect, m_total_down, m_equal]

if __name__ == '__main__':
    for tag in sys.argv[1:]:
        print(tag, analyse(tag))
