"""Node fields of the links downstream of alexandria/ragusa/wien at a chosen save."""
import sys
sys.path.insert(0, 'scripts/research')
import venice_load as V
from venice_load import as_list
tag = sys.argv[1] if len(sys.argv) > 1 else '1445_04_01'
p = [x for x in V.files() if x.stem.endswith(tag)][0]
ns = V.nodes(p); names = [n['definitions'] for n in ns]
by = dict(zip(names, ns))
out = {n: [] for n in names}
for i, n in enumerate(ns):
    for inc in as_list(n.get('incoming')):
        if isinstance(inc, dict) and 'from' in inc:
            out[names[int(inc['from']) - 1]].append(names[i])
F = ['local_value', 'current', 'outgoing', 'total', 'p_pow', 'max', 'collector_power', 'pull_power', 'retain_power', 'retention', 'num_collectors', 'highest_power']
for src in ['alexandria', 'ragusa', 'wien']:
    print(src, 'weights', by[src].get('steer_power'), 'links', out[src])
    for l in out[src]:
        print('   ', l, {k: by[l].get(k) for k in F})
