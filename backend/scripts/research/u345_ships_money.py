"""Collecting entries where only ships changed: is the rest of the node unchanged (then dmoney is the ship effect)?"""
import sys
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from u345_ships_diff import table
from u345_ships_maxpow import f
E = {e['id']: e for e in L.OLD + L.NEW}
def nodeinfo(e):
    return {n['definitions']: dict(cur=f(n, 'current'), total=f(n, 'total'), retain=f(n, 'retain_power'), pull=f(n, 'pull_power'), local=f(n, 'local_value'), out=f(n, 'outgoing'), ret=f(n, 'retention')) for n in common.nodes(e)}
for a, b in (('U03', 'U04'), ('U04', 'U05'), ('U03', 'U05')):
    ta, tb = table(E[a]), table(E[b]); na, nb = nodeinfo(E[a]), nodeinfo(E[b])
    print('==', a, '->', b)
    for k in sorted(set(ta) & set(tb)):
        x, y = ta[k], tb[k]
        if abs(x['sp'] - y['sp']) < 0.0005 or not y['collect']: continue
        same = abs(x['pp'] - y['pp']) < 0.0015 and abs(x['prev'] - y['prev']) < 0.0015 and x['cap'] == y['cap'] and abs(x['mods'] - y['mods']) < 0.0015 and x['tr'] == y['tr']
        if not same: continue
        node = k[0]
        others = [kk for kk in ta if kk[0] == node and kk != k and kk in tb and (abs(ta[kk]['mp'] - tb[kk]['mp']) > 0.0015 or abs(ta[kk]['pp'] - tb[kk]['pp']) > 0.0015)]
        print(f"   {k[1]} {node}: ships {x['ls']}->{y['ls']}; val {x['val']:.3f}->{y['val']:.3f}; money {x['money']:.3f}->{y['money']:.3f}; other entries in node changed power: {len(others)}; "
              f"node current {na[node]['cur']:.3f}->{nb[node]['cur']:.3f} local {na[node]['local']:.3f}->{nb[node]['local']:.3f} retain_power {na[node]['retain']:.3f}->{nb[node]['retain']:.3f}")
