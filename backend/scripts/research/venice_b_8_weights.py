"""R08 Q1 on the Venice series: node weights vs sums over steerers on each link (val, val*add, ...)."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V
from venice_load import as_list

def steerers(n, nlinks):
    """{link: [(country, entry)]} for entries with type (non-collecting merchant) incl. recalled leftovers with add."""
    g = collections.defaultdict(list)
    for c, e in n.items():
        if isinstance(e, dict) and c.isupper() and (e.get('type') or 'add' in e):
            g[int(e.get('steer_power', 0))].append((c, e))
    return g

def predict(n, nlinks, f):
    g = steerers(n, nlinks)
    xs = [sum(f(c, e) for c, e in g.get(l, [])) for l in range(nlinks)]
    s = sum(xs)
    return [x / s for x in xs] if s > 0 else None

MODELS = {
    'val': lambda c, e: e.get('val', 0),
    'max_pow': lambda c, e: e.get('max_pow', 0),
    'val*add': lambda c, e: e.get('val', 0) * e.get('add', 0),
    'val*(1+add)': lambda c, e: e.get('val', 0) * (1 + e.get('add', 0)),
    'prev': lambda c, e: e.get('prev', e.get('max_pow', 0)),
}

def run(tag, show=0):
    p = [x for x in V.files() if x.stem.endswith(tag)][0]
    ns = V.nodes(p); names = [n['definitions'] for n in ns]
    nl = collections.Counter()
    for n in ns:
        for inc in as_list(n.get('incoming')):
            if isinstance(inc, dict) and 'from' in inc: nl[names[int(inc['from']) - 1]] += 1
    res = collections.defaultdict(lambda: [0, 0]); allsteer = [0, 0]
    for n in ns:
        k = nl[n['definitions']]; w = n.get('steer_power')
        if k < 2 or not isinstance(w, list) or not (n.get('outgoing') or 0) > 0: continue
        if not steerers(n, k): continue
        for name, f in MODELS.items():
            pr = predict(n, k, f)
            if pr is None: continue
            ok = max(abs(a - b) for a, b in zip(pr, w)) < 0.0025
            res[name][0] += ok; res[name][1] += 1
            if show and name == show and not ok and n['definitions'] in ('alexandria', 'ragusa', 'wien'):
                print('   ', n['definitions'], [round(x, 3) for x in pr], w)
    return {k: tuple(v) for k, v in res.items()}

if __name__ == '__main__':
    for tag in sys.argv[1:]:
        print(tag, run(tag, show='val'))
