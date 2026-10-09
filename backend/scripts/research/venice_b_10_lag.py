"""R08 Q1: do the weights use the entries' val of the previous tick (lag)? tag = save with weights; ref = save whose vals are used."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V
import venice_b_8_weights as W
from venice_load import as_list

def valmap(p, key='val'):
    d = {}
    for n in V.nodes(p):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and key in e:
                d[(n['definitions'], c)] = e[key]
    return d

def run(tag, ref, key='val'):
    by = {p.stem[6:]: p for p in V.files()}
    ns = V.nodes(by[tag]); names = [n['definitions'] for n in ns]
    vm = valmap(by[ref], key)
    nl = collections.Counter()
    for n in ns:
        for inc in as_list(n.get('incoming')):
            if isinstance(inc, dict) and 'from' in inc: nl[names[int(inc['from']) - 1]] += 1
    ok = tot = 0; bad = []
    for n in ns:
        k = nl[n['definitions']]; w = n.get('steer_power')
        if k < 2 or not isinstance(w, list) or not (n.get('outgoing') or 0) > 0: continue
        if not W.steerers(n, k): continue
        pr = W.predict(n, k, lambda c, e: vm.get((n['definitions'], c), e.get('val', 0)))
        if pr is None: continue
        tot += 1
        err = max(abs(x - y) for x, y in zip(pr, w)); ok += err < 0.0025
        bad.append((round(err, 4), n['definitions']))
    return ok, tot, sorted(bad, reverse=True)[:4]

if __name__ == '__main__':
    for a in sys.argv[1:]:
        tag, ref = a.split(':')
        print(tag, 'vals of', ref, run(tag, ref))
