"""Venice series R04: transfer entries (t_out/t_in/t_to/t_from) per save; ratio t_out/val and the giver's overlord / subject data."""
import sys
sys.path.insert(0, "scripts/research")
import venice_load as V
from final_r12_common import entries_of
for p in V.files():
    C = V.load(p, 'countries'); rows = []
    for n in V.nodes(p):
        for t, e in entries_of(n).items():
            if 't_out' in e:
                exp = int((0.5 * e['val'] - 0.05) * 1000) / 1000
                rows.append((n['definitions'], t, e['val'], e['t_out'], 'half' if abs(e['t_out'] - exp) < 0.0015 else 'val-0.1' if abs(e['val'] - e['t_out'] - 0.1) < 0.0015 else 'other'))
    gv = sorted({r[1] for r in rows})
    print(p.stem[6:], len(rows), gv, [r for r in rows][:3], {g: (C[g].get('overlord'), C[g].get('transfer_trade_power_to')) for g in gv if isinstance(C.get(g), dict)})
