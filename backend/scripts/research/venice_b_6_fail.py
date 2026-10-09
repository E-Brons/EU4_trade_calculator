import sys
sys.path.insert(0, 'scripts/research')
import venice_load as V
tag, node, link = sys.argv[1], sys.argv[2], int(sys.argv[3])
p = [x for x in V.files() if x.stem.endswith(tag)][0]
n = [x for x in V.nodes(p) if x['definitions'] == node][0]
print(node, 'w', n.get('steer_power'))
rows = []
for c, e in n.items():
    if isinstance(e, dict) and c.isupper() and (e.get('steer_power', 0) == link) and ('add' in e or 'type' in e or 'steer_power' in e):
        rows.append((e.get('val', 0), c, e))
for v, c, e in sorted(rows, key=lambda r: -r[0]):
    print('  ', c, {k: e[k] for k in e if k != 'max_demand'})
