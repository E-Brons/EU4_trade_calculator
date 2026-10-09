"""Diff U03->U04->U05 (and S79->S80 for reference): entries whose ships changed while province_power/prev/extras/max_demand did not."""
import sys, json
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from u345_ships_maxpow import f, A
from collections import Counter
BASE = {k: v['trade_power'] for k, v in json.load(open('data/game/light_ships.json'))['ships'].items()}

def table(e):
    t = {}
    for n in common.nodes(e):
        for tag, c in n.items():
            if isinstance(c, dict) and 'max_pow' in c:
                mods = sum(f(m, 'power') for m in A(c.get('modifier')) if isinstance(m, dict))
                t[(n['definitions'], tag)] = dict(pp=f(c, 'province_power'), sp=f(c, 'ship_power'), ls=int(f(c, 'light_ship')), prev=f(c, 'prev'),
                    mp=f(c, 'max_pow'), md=f(c, 'max_demand'), val=f(c, 'val'), money=f(c, 'money'), cap=bool(c.get('has_capital')), mods=mods,
                    tr=bool(c.get('has_trader')), collect='total' in c, steer='type' in c, tin=f(c, 't_in'), tout=f(c, 't_out'))
    return t

def compare(a, b, label):
    ta, tb = table(a), table(b)
    only_ship, ship_changed = [], 0
    for k in set(ta) & set(tb):
        x, y = ta[k], tb[k]
        if abs(x['sp'] - y['sp']) < 0.0005: continue
        ship_changed += 1
        same = abs(x['pp'] - y['pp']) < 0.0015 and abs(x['prev'] - y['prev']) < 0.0015 and x['cap'] == y['cap'] and abs(x['mods'] - y['mods']) < 0.0015 \
            and x['tr'] == y['tr'] and abs(x['tin'] - y['tin']) < 0.0015 and abs(x['tout'] - y['tout']) < 0.0015
        if same: only_ship.append((k, x, y))
    print(f"== {label}: entries present in both {len(set(ta) & set(tb))}; ship_power changed in {ship_changed}; of those with pp/prev/extras/transfers unchanged: {len(only_ship)}")
    ok_mp = ok_val = ok_md = 0
    for k, x, y in sorted(only_ship):
        dsp = y['sp'] - x['sp']; dmp = y['mp'] - x['mp']
        ok_mp += abs(dmp - dsp) <= 0.0025
        dmd = y['md'] - x['md']; ok_md += abs(dmd) < 0.0015
        dval_pred = y['mp'] * y['md'] - x['mp'] * x['md']
        ok_val += abs((y['val'] - x['val']) - dval_pred) <= 0.0025
        print(f"   {k[1]:>4} {k[0]:<18} ships {x['ls']:>3}->{y['ls']:>3} ship_power {x['sp']:8.3f}->{y['sp']:8.3f} (d {dsp:+8.3f}) max_pow d {dmp:+8.3f} max_demand {x['md']:.3f}->{y['md']:.3f} val {x['val']:8.3f}->{y['val']:8.3f} money {x['money']:7.3f}->{y['money']:7.3f} {'collect' if y['collect'] else 'steer' if y['steer'] else 'passive'}")
    if only_ship: print(f"   d(max_pow) == d(ship_power) in {ok_mp}/{len(only_ship)}; max_demand unchanged in {ok_md}/{len(only_ship)}; d(val) == d(max_pow*max_demand) in {ok_val}/{len(only_ship)}")
    return only_ship

if __name__ == '__main__':
    E = {e['id']: e for e in L.OLD + L.NEW}
    for a, b in (('S79', 'S80'), ('U03', 'U04'), ('U04', 'U05'), ('U03', 'U05')):
        compare(E[a], E[b], f'{a} -> {b}')
