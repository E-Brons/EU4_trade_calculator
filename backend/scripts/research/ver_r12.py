"""Independent recomputation of R12/R08 link claims. Reports counts over all 82 saves (as the responses do) and over 80 unique saves."""
import sys; sys.path.insert(0, 'scripts/research')
from collections import Counter
from ver_common import *

def run(ids):
    C = Counter(); mism_noadd = []
    for sid in ids:
        ns = nodes_of(sid)
        order = [n[0] for n in ns]
        byid = {n[0]: n for n in ns}
        # incoming index: target -> {source: (value, add)}
        inc = {}
        for nid, raw, ents in ns:
            for i in lst(raw.get('incoming')):
                if isinstance(i, dict):
                    src = order[int(i['from']) - 1]
                    inc.setdefault(nid, {}).setdefault(src, []).append((fl(i['value']), fl(i.get('add'), 0.0)))
        for nid, raw, ents in ns:
            targets = [o['target'] for o in GRAPH.get(nid, {}).get('outgoing', [])]
            out = fl(raw.get('outgoing'))
            if not targets or out is None: continue
            links = []
            for t in targets:
                l = inc.get(t, {}).get(nid)
                if l is None or len(l) != 1: links = None; break
                links.append(l[0])
            if links is None: C['skipped']+=1; continue
            k = len(targets)
            w = [float(x) for x in lst(raw.get('steer_power'))]
            S = sum(v for v, a in links); A = sum(a for v, a in links)
            C['nodes'] += 1
            C['sum_eq_out_0.0015k'] += abs(S - out) <= 0.0015 * k
            C['sum-add_eq_out_0.0015k'] += abs(S - A - out) <= 0.0015 * k
            C['any_add'] += A > 0
            C['vao_eq_out_0.0005'] += abs(fl(raw.get('value_added_outgoing'), out) - out) <= 0.0005
            C['vao_present'] += 'value_added_outgoing' in raw
            if abs(S - out) > 0.0015 * k and A == 0: C['mismatch_no_add'] += 1
            # node bound
            if len(w) == k:
                C['bound_ok'] += abs((S - A) - out) <= out * (1 - sum(w)) + 0.003 * k + 0.001 * out * k
                C['w_sum_' + str(round(sum(w), 3))] += 1
                for i, (v, a) in enumerate(links):
                    C['links'] += 1
                    C['link_val_bound'] += (out * w[i] - 0.002) <= (v - a) <= (out * (w[i] + 0.001) + 0.002)
                    # steerers on link i: entries with 'type' and steer_power==i (absent steer_power => link 0) and an 'add'
                    sa = sum(fl(e.get('add'), 0.0) for e in ents.values() if 'type' in e and int(fl(e.get('steer_power'), 0)) == i)
                    C['link_add'] += abs(a - out * w[i] * sa) <= 0.0015 + 0.0006 * out + 0.01 * abs(a)
                    if abs(a - out * w[i] * sa) > 0.0015 + 0.0006 * out + 0.01 * abs(a): mism_noadd.append((sid, nid, i, a, round(out*w[i]*sa,4)))
    return C, mism_noadd

if __name__ == '__main__':
    for label, ids in (('all 82', list(ENT)), ('80 unique', [i for i in ENT if i not in DUP])):
        C, bad = run(ids)
        print(label, dict(C)); print('  link_add misses', bad[:6])
