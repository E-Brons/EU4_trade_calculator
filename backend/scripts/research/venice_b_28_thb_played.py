"""R09 Q8 on the played saves: thb/0.1 vs (steering merchants, away collectors) using the same table as venice_b_26 table2."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import common
for e in common.entries():
    if e['id'] not in ('S79', 'S80', 'U03', 'U04', 'U05', 'U06'): continue
    ns = common.nodes(e); cs = common.block(e, 'countries')
    steer = collections.Counter(); away = collections.Counter(); home = {}
    for n in ns:
        for c, x in n.items():
            if isinstance(x, dict) and c.isupper() and x.get('has_capital'): home[c] = n['definitions']
    for n in ns:
        for c, x in n.items():
            if isinstance(x, dict) and c.isupper() and x.get('has_trader'):
                if x.get('type'): steer[c] += 1
                elif not x.get('has_capital'): away[c] += 1
    ok = tot = 0; bad = collections.Counter()
    for c, d in cs.items():
        if not isinstance(d, dict) or 'transfer_home_bonus' not in d or c not in home: continue
        pred = 0 if away[c] else steer[c]
        got = round(d['transfer_home_bonus'] / 0.1)
        tot += 1; ok += pred == got
        if pred != got: bad[(steer[c], away[c], got)] += 1
    print(e['id'], e['date'], ok, '/', tot, dict(bad.most_common(6)))
