"""R08 Q1: weight_l ∝ sum over steerers on l of val_c * a_c, with a_c the country-level strength = add * rank (rank by val within the link)."""
import sys, collections, statistics
sys.path.insert(0, 'scripts/research')
import venice_load as V
import venice_b_5_rank as R
import venice_b_8_weights as W
from venice_load import as_list

def country_a(ns):
    g = R.steer_groups(ns)
    est = collections.defaultdict(list)
    for (node, link), lst in g.items():
        lst = sorted(lst, key=lambda ce: -ce[1].get('val', 0))
        for r, (c, e) in enumerate(lst, 1):
            est[c].append((e['add'] + 0.0005) * r)   # truncated add: centre of [add, add+0.001)
    # robust: the median of the per-node estimates
    return {c: statistics.median(v) for c, v in est.items()}

def run(tag, verbose=False):
    p = [x for x in V.files() if x.stem.endswith(tag)][0]
    ns = V.nodes(p); names = [n['definitions'] for n in ns]
    a = country_a(ns)
    nl = collections.Counter()
    for n in ns:
        for inc in as_list(n.get('incoming')):
            if isinstance(inc, dict) and 'from' in inc: nl[names[int(inc['from']) - 1]] += 1
    ok = tot = 0; rows = []
    amean = statistics.mean(a.values())
    for n in ns:
        k = nl[n['definitions']]; w = n.get('steer_power')
        if k < 2 or not isinstance(w, list) or not (n.get('outgoing') or 0) > 0: continue
        g = W.steerers(n, k)
        if not g: continue
        f = lambda c, e: e.get('val', 0) * a.get(c, amean)
        pr = W.predict(n, k, f)
        if pr is None: continue
        tot += 1
        err = max(abs(x - y) for x, y in zip(pr, w))
        ok += err < 0.0025
        rows.append((err, n['definitions'], [round(x, 3) for x in pr], w))
    if verbose:
        for r in sorted(rows, reverse=True)[:8]: print('   ', r)
    return ok, tot

if __name__ == '__main__':
    for tag in sys.argv[1:]:
        print(tag, run(tag, verbose=True))
