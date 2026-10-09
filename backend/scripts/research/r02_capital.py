"""R02 Q4: which node carries `has_capital`: node of country.capital province, or node of country.trade_port?  Colonial nations (C00-C17...)?"""
import sys, os, re, collections, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
c = collections.Counter(); diff_ex = []; away_c = collections.Counter()
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    ps = common.block(e, 'provinces')
    pn = {abs(int(k)): p.get('trade') for k, p in ps.items() if isinstance(p, dict) and 'trade' in p}
    hc = collections.defaultdict(set)
    for n in m['nodes']:
        for k, v in n.items():
            if TAG.match(k) and isinstance(v, dict) and v.get('has_capital'): hc[k].add(n['definitions'])
    for tag, cc in m['countries'].items():
        try:
            capn = pn.get(int(cc['capital'])); portn = pn.get(int(cc['trade_port']))
        except Exception:
            continue
        if capn is None and portn is None: continue
        h = hc.get(tag, set())
        key = ('has_capital node == node(trade_port)' if h == {portn} else 'has_capital node == node(capital)' if h == {capn} else ('no has_capital entry' if not h else 'neither'))
        if capn != portn: key = 'CAPITAL!=PORT NODE: ' + key
        c[key] += 1
        if capn != portn and len(diff_ex) < 5: diff_ex.append((e['id'], tag, 'capital node', capn, 'port node', portn, 'has_capital at', sorted(h)))
        if re.fullmatch(r'C\d\d', tag):
            away_c[('colonial nation', 'has a has_capital entry' if h else 'no has_capital entry')] += 1
for k, v in sorted(c.items()): print(v, k)
print(diff_ex); print(dict(away_c))
