"""Venice series: (1) merchant entries with R=0 mid-month / no-merchant entries with R=2 - were they already in that state at the last 1st?  (2) U25->U27 recall rows (max_pow, add, weights)."""
import sys, collections
sys.path.insert(0, "scripts/research")
import venice_load as V
from final_r12_common import entries_of, lst

FS = {p.stem[6:]: p for p in V.files()}
def ents(s):
    out = {}
    for n in V.nodes(FS[s]):
        for t, e in entries_of(n).items():
            if 'max_pow' in e and 'modifier' not in e:
                out[(n['definitions'], t)] = (bool(e.get('has_trader')), round(e['max_pow'] - e.get('province_power', 0) - e.get('ship_power', 0) - e.get('prev', 0) - 5 * bool(e.get('has_capital')), 3))
    return out

def arrivals(tick, s):
    a, b = ents(tick), ents(s)
    zero_m = [k for k, (h, r) in b.items() if h and r == 0.0]
    two_n = [k for k, (h, r) in b.items() if not h and r == 2.0]
    z = collections.Counter(('had_trader_at_tick' if a.get(k, (False,))[0] else ('no_trader_at_tick' if k in a else 'entry_new')) for k in zero_m)
    t = collections.Counter(('had_trader_at_tick' if a.get(k, (False,))[0] else ('no_trader_at_tick' if k in a else 'entry_new')) for k in two_n)
    print(f"{tick} -> {s}: merchant entries with R=0: {len(zero_m)} {dict(z)} | no-merchant entries with R=2: {len(two_n)} {dict(t)}")

for tick, s in [('1444_12_01', '1444_12_02'), ('1444_12_01', '1444_12_11'), ('1444_12_01', '1444_12_31'), ('1445_01_01', '1445_01_15'), ('1445_03_01', '1445_03_31')]:
    arrivals(tick, s)

print('--- recall rows')
for s in ('1445_03_01', '1445_03_31', '1445_04_01', '1445_05_01', '1445_06_01', '1445_07_02'):
    ns = {n['definitions']: n for n in V.nodes(FS[s])}
    row = []
    for nd in ('alexandria', 'ragusa', 'wien'):
        e = ns[nd]['VEN']
        row.append((nd, 'has_trader' if e.get('has_trader') else '-', 'type' if 'type' in e else '-', e.get('add'), e['max_pow'], lst(ns[nd].get('steer_power'))))
    print(s, row)
