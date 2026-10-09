"""R09/R06: node entries carrying a `modifier` block (merchant_recalled) and how `duration` moves between saves."""
import sys
sys.path.insert(0, 'scripts/research')
import venice_load as V
prev = {}
for p in V.files():
    cur = {}
    for n in V.nodes(p):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and isinstance(e.get('modifier'), dict): cur[(n['definitions'], c)] = e['modifier']
    tag = p.stem[6:]
    for k, m in cur.items():
        d0 = prev.get(k, {}).get('duration')
        print(tag, k, m, 'change since previous save:', (m.get('duration') - d0) if d0 is not None and m.get('duration') is not None else 'new')
    prev = cur
