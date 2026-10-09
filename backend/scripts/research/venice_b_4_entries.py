import sys
sys.path.insert(0, 'scripts/research')
import venice_load as V
tag, node = sys.argv[1], sys.argv[2]
p = [x for x in V.files() if x.stem.endswith(tag)][0]
n = [x for x in V.nodes(p) if x['definitions'] == node][0]
print(node, tag, 'w', n.get('steer_power'), 'out', n.get('outgoing'), 'cur', n.get('current'), 'total', n.get('total'))
for c, e in n.items():
    if isinstance(e, dict) and c.isupper() and any(k in e for k in ('type', 'add', 'steer_power', 'has_trader', 'money', 't_in', 't_out')):
        print('  ', c, {k: e[k] for k in e if k not in ('max_demand',)})
print('incoming', n.get('incoming'))
