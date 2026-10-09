"""Venice series, merchant topics: per-save table of VEN entries, node weights, add, transfer_home_bonus."""
import sys
sys.path.insert(0, 'scripts/research')
import venice_load as V
from venice_load import as_list

NODES = ['alexandria', 'ragusa', 'wien', 'venice']
for p in V.files():
    ns = {n['definitions']: n for n in V.nodes(p)}
    c = V.load(p, 'countries')['VEN']
    print('==', p.stem[6:], 'thb', c.get('transfer_home_bonus'))
    for nm in NODES:
        n = ns[nm]; t = n.get('VEN', {})
        keep = {k: t[k] for k in ('type', 'val', 'prev', 'max_pow', 'max_demand', 'steer_power', 'add', 'has_trader', 'money', 'total', 'province_power', 'power_fraction') if k in t}
        print('  ', nm, 'w', n.get('steer_power'), 'cur', n.get('current'), 'out', n.get('outgoing'), 'ret', n.get('retention'), keep)
