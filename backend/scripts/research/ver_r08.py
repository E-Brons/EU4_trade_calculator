import sys; sys.path.insert(0, 'scripts/research')
from collections import Counter, defaultdict
from ver_common import *
PL = ['S79', 'S80']
# (a) add key counts
for label, ids in (('82', list(ENT)), ('unique', [i for i in ENT if i not in DUP])):
    c = Counter()
    for sid in ids:
        for nid, raw, ents in nodes_of(sid):
            for t, e in ents.items():
                if 'add' in e: c['add_type' if 'type' in e else 'add_notype'] += 1; c['add_in_'+('start' if sid in STARTS else 'played')] += 1
    print('(a)', label, dict(c))
# (b) start snapshots equal weights
b = Counter()
for sid in STARTS:
    for nid, raw, ents in nodes_of(sid):
        k = len(GRAPH.get(nid, {}).get('outgoing', []))
        w = [float(x) for x in lst(raw.get('steer_power'))]
        if k >= 2 and len(w) == k and any('type' in e for e in ents.values()):
            b['nodes_steerers_k>=2'] += 1
            b['equal'] += (max(w) - min(w) < 1e-9)
print('(b)', dict(b))
# (c) identity 2 with add-key entries vs type entries
c = Counter()
for sid in [i for i in ENT if i not in DUP]:
    ns = nodes_of(sid); order = [n[0] for n in ns]
    inc = {}
    for nid, raw, ents in ns:
        for i in lst(raw.get('incoming')):
            if isinstance(i, dict): inc.setdefault(nid, {}).setdefault(order[int(i['from']) - 1], []).append((fl(i['value']), fl(i.get('add'), 0.0)))
    for nid, raw, ents in ns:
        t = [o['target'] for o in GRAPH.get(nid, {}).get('outgoing', [])]; out = fl(raw.get('outgoing'))
        w = [float(x) for x in lst(raw.get('steer_power'))]
        if not t or out is None or len(w) != len(t): continue
        L = [inc.get(x, {}).get(nid) for x in t]
        if any(l is None or len(l) != 1 for l in L): continue
        for i, l in enumerate(L):
            v, a = l[0]
            for mode in ('type', 'addkey'):
                sa = sum(fl(e.get('add'), 0) for e in ents.values() if 'add' in e and (mode == 'addkey' or 'type' in e) and int(fl(e.get('steer_power'), 0)) == i)
                c[mode + '_ok'] += abs(a - out * w[i] * sa) <= 0.0015 + 0.0006 * out + 0.01 * abs(a)
            c['links'] += 1
print('(c) unique-80', dict(c))
# (d) example rows
for sid, node in (('S79', 'alexandria'), ('S79', 'gulf_of_aden')):
    ns = nodes_of(sid); order = [n[0] for n in ns]
    nd = [n for n in ns if n[0] == node][0]
    print('(d)', sid, node, 'outgoing', nd[1].get('outgoing'), 'w', nd[1].get('steer_power'))
    for tn, raw, ents in ns:
        for i in lst(raw.get('incoming')):
            if isinstance(i, dict) and order[int(i['from']) - 1] == node:
                print('    ->', tn, 'value', i['value'], 'add', i.get('add'))
    k = len(GRAPH[node]['outgoing']); sums = defaultdict(float)
    for t, e in nd[2].items():
        if 'add' in e: sums[int(fl(e.get('steer_power'), 0))] += e['add']
    print('    sum add per link', dict(sums))
