"""R08 Q2: is `add` = a_country / rank, with rank = order among the steerers of the same link (by val / max_pow / prev)?

For every save: group entries carrying `add` by (node, link), rank them by a key, and check for each country that add*rank is constant
(within rank*0.001 truncation) across all its steering entries of that save.
"""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V
from venice_load import as_list

KEYS = {
    'val': lambda e: -e.get('val', 0),
    'max_pow': lambda e: -e.get('max_pow', 0),
    'prev': lambda e: -e.get('prev', 0),
    'val_then_name': lambda e: (-e.get('val', 0), 0),
}

def steer_groups(ns):
    g = collections.defaultdict(list)
    for n in ns:
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and 'add' in e:
                g[(n['definitions'], e.get('steer_power', 0))].append((c, e))
    return g

def test(ns, key):
    g = steer_groups(ns)
    per = collections.defaultdict(list)
    for (node, link), lst in g.items():
        lst = sorted(lst, key=lambda ce: KEYS[key](ce[1]))
        for r, (c, e) in enumerate(lst, 1):
            per[c].append((e['add'], r, node, link))
    ok = tot = 0
    bad = []
    for c, rows in per.items():
        # a_c = add * rank estimated from rank-1 rows if present else the max estimate
        est = [a * r for a, r, _, _ in rows]
        ref = max(est)
        for a, r, node, link in rows:
            tot += 1
            lo, hi = a * r, (a + 0.001) * r
            if lo - 1e-9 <= ref + 0.0011 and ref - 0.0011 <= hi + 0.0011 * r:
                ok += 1
            else:
                bad.append((c, node, link, a, r, round(a * r, 4), round(ref, 4)))
    return ok, tot, bad

if __name__ == '__main__':
    tags = sys.argv[1:]
    for tag in tags:
        p = [x for x in V.files() if x.stem.endswith(tag)][0]
        ns = V.nodes(p)
        for key in ('val', 'max_pow', 'prev'):
            ok, tot, bad = test(ns, key)
            print(tag, key, ok, '/', tot, bad[:4])
