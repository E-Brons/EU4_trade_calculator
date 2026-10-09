"""R09: VEN num_ships_protecting_trade vs the light_ship / ship_power entries (where the fleet is, per save)."""
import sys
sys.path.insert(0, 'scripts/research')
import venice_load as V
for p in V.files():
    c = V.load(p, 'countries')['VEN']; s = 0; where = []
    for n in V.nodes(p):
        e = n.get('VEN')
        if isinstance(e, dict) and e.get('light_ship'): s += e['light_ship']; where.append((n['definitions'], e['light_ship'], e.get('ship_power')))
    print(p.stem[6:], 'num_ships_protecting_trade', c.get('num_ships_protecting_trade'), 'sum light_ship', s, where, 'trade_mission', c.get('trade_mission'))
