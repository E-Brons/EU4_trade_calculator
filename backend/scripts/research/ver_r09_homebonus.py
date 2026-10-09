"""Independent check of transfer_home_bonus claims (played saves only; start saves are zero everywhere)."""
import sys, re, collections
sys.path.insert(0, 'scripts/research')
import common
from app.parsing.tradenodes import load_trade_graph
g = load_trade_graph(); TAG = re.compile(r'^[A-Z0-9]{2,4}$'); PLAYED = ('S79', 'S80', 'U01', 'U02')
S = collections.Counter(); ex = []
for e in common.entries():
    if e['id'] not in PLAYED: continue
    cs = common.block(e, 'countries'); ns = common.nodes(e); cap = {}
    for n in ns:
        for t, v in n.items():
            if TAG.match(t) and isinstance(v, dict) and v.get('has_capital'): cap[t] = n['definitions']
    into = collections.Counter(); away = collections.Counter(); steer_any = collections.Counter()
    for n in ns:
        nid = n['definitions']; outs = g.outgoing(nid) if nid in g else ()
        for t, v in n.items():
            if not (TAG.match(t) and isinstance(v, dict)): continue
            if 'type' in v and v.get('has_trader'):
                li = int(v.get('steer_power', 0)); tgt = outs[li] if li < len(outs) else None
                steer_any[t] += 1
                if tgt is not None and cap.get(t) == tgt: into[t] += 1
            if 'total' in v and v.get('has_trader') and t in cap and cap[t] != nid: away[t] += 1
    for t, c in cs.items():
        if not isinstance(c, dict) or 'transfer_home_bonus' not in c: continue
        b = round(c['transfer_home_bonus'], 3)
        S['country_saves'] += 1
        if b > 0:
            S['nonzero'] += 1; S['nonzero_with_capital_entry'] += t in cap
            if t in cap:
                S['nz_cap: into>=1'] += into[t] >= 1; S['nz_cap: away==0'] += away[t] == 0
                S['nz_cap: b==0.1*into'] += abs(b - min(0.1 * into[t], 1.0)) < 0.0015
        elif t in cap and into[t] >= 1:
            S['zero_with_cap_and_into>=1 (played saves)'] += 1
print(dict(S))
