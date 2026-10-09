"""R08 Q2 follow-up: rank by val of the current save vs val of the previous-tick save (lag)."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V
import venice_b_5_rank as R

files = V.files()
by = {p.stem[6:]: p for p in files}
def valmap(p):
    d = {}
    for n in V.nodes(p):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and 'val' in e:
                d[(n['definitions'], c)] = e['val']
    return d

def test(cur, ref):
    ns = V.nodes(by[cur]); vm = valmap(by[ref])
    g = R.steer_groups(ns)
    per = collections.defaultdict(list)
    for (node, link), lst in g.items():
        lst = sorted(lst, key=lambda ce: -vm.get((node, ce[0]), ce[1].get('val', 0)))
        for r, (c, e) in enumerate(lst, 1):
            per[c].append((e['add'], r, node, link))
    ok = tot = 0; bad = []
    for c, rows in per.items():
        ref_a = max(a * r for a, r, *_ in rows)
        for a, r, node, link in rows:
            tot += 1
            if a * r - 0.0011 <= ref_a <= (a + 0.001) * r + 0.0011: ok += 1
            else: bad.append((c, node, link, a, r))
    return ok, tot, bad

if __name__ == '__main__':
    for cur, ref in [a.split(':') for a in sys.argv[1:]]:
        ok, tot, bad = test(cur, ref)
        print(cur, 'rank by val of', ref, ok, '/', tot, bad[:3])
