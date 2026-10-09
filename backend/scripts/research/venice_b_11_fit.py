"""R08 Q1: homogeneous least squares for w_l ∝ sum_f beta_f * F_{l,f}; F = per-link sums over steerers. Reports the best beta and the exact-match count."""
import sys, collections, statistics
sys.path.insert(0, 'scripts/research')
import numpy as np
import venice_load as V
import venice_b_8_weights as W
import venice_b_9_weights_a as A
from venice_load import as_list

FEATS = {
    'val': lambda c, e, a: e.get('val', 0),
    'val*a': lambda c, e, a: e.get('val', 0) * a,
    'n': lambda c, e, a: 1.0,
    'prev': lambda c, e, a: e.get('prev', 0),
    'add': lambda c, e, a: e.get('add', 0),
    'val*add': lambda c, e, a: e.get('val', 0) * e.get('add', 0),
}

def build(tag, feats):
    p = [x for x in V.files() if x.stem.endswith(tag)][0]
    ns = V.nodes(p); names = [n['definitions'] for n in ns]
    a = A.country_a(ns); amean = statistics.mean(a.values())
    nl = collections.Counter()
    for n in ns:
        for inc in as_list(n.get('incoming')):
            if isinstance(inc, dict) and 'from' in inc: nl[names[int(inc['from']) - 1]] += 1
    items = []
    for n in ns:
        k = nl[n['definitions']]; w = n.get('steer_power')
        if k < 2 or not isinstance(w, list) or not (n.get('outgoing') or 0) > 0: continue
        g = W.steerers(n, k)
        if not g: continue
        F = np.array([[sum(FEATS[f](c, e, a.get(c, amean)) for c, e in g.get(l, [])) for f in feats] for l in range(k)])
        items.append((n['definitions'], F, np.array(w)))
    return items

def fit(items):
    rows = []
    for name, F, w in items:
        k = len(w)
        for l in range(k):
            for m in range(l + 1, k):
                rows.append(w[m] * F[l] - w[l] * F[m])
    M = np.array(rows)
    u, s, vt = np.linalg.svd(M)
    b = vt[-1]
    if b.sum() < 0: b = -b
    return b / abs(b).max(), s

def score(items, b):
    ok = 0; worst = []
    for name, F, w in items:
        x = F @ b
        if x.sum() <= 0 or (x < 0).any(): continue
        pr = x / x.sum(); err = abs(pr - w).max(); ok += err < 0.0025; worst.append((round(err, 4), name))
    return ok, len(items), sorted(worst, reverse=True)[:3]

if __name__ == '__main__':
    tag = sys.argv[1]
    for feats in (['val'], ['val', 'n'], ['val', 'val*a'], ['val', 'val*a', 'n'], ['val', 'prev'], ['val', 'add', 'val*add'], ['val', 'prev', 'val*a', 'n']):
        items = build(tag, feats)
        b, s = fit(items)
        print(tag, feats, np.round(b, 3), score(items, b))
