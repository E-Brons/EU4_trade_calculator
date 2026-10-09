"""Verifier (independent): node carrying has_capital vs node of trade_port / capital province."""
import sys, collections, re
sys.path.insert(0, 'scripts/research')
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
C = collections.Counter()
for e in common.entries():
    ps = common.block(e, 'provinces'); cs = common.block(e, 'countries')
    pn = {abs(int(k)): p['trade'] for k, p in ps.items() if isinstance(p, dict) and 'trade' in p}
    hc = collections.defaultdict(list)
    for n in common.nodes(e):
        for k, v in n.items():
            if TAG.match(k) and isinstance(v, dict) and v.get('has_capital'): hc[k].append(n['definitions'])
    for tag, c in cs.items():
        if not isinstance(c, dict) or 'trade_port' not in c: continue
        port = pn.get(int(c['trade_port'])); cap = pn.get(int(c['capital'])) if 'capital' in c else None
        C['countries'] += 1
        if tag in hc:
            C['has_capital entries'] += 1
            C['...at node(trade_port)'] += hc[tag] == [port]
            C['...at node(capital)'] += hc[tag] == [cap]
            C['...multiple nodes'] += len(hc[tag]) > 1
        else: C['no has_capital'] += 1
        C['node(capital)!=node(trade_port)'] += cap != port
print(dict(C))
