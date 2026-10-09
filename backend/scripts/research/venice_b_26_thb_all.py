"""R09 Q8 across all countries of a save: transfer_home_bonus / 0.1 vs the number of merchants steering (entries with `type`), collecting (has_trader, no type), and merchants steering INTO the home node."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V
from venice_load import as_list

def run(tag):
    p = [x for x in V.files() if x.stem.endswith(tag)][0]
    ns = V.nodes(p); names = [n['definitions'] for n in ns]
    out = collections.defaultdict(list)
    for n in ns:
        for inc in as_list(n.get('incoming')):
            if isinstance(inc, dict) and 'from' in inc: out[names[int(inc['from']) - 1]].append(n['definitions'])
    cs = V.load(p, 'countries')
    steer = collections.Counter(); coll = collections.Counter(); into_home = collections.Counter(); home = {}
    for n in ns:
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('has_capital'): home[c] = n['definitions']
    for n in ns:
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper():
                if e.get('type') and e.get('has_trader'):
                    steer[c] += 1
                    link = int(e.get('steer_power', 0)); tgt = out[n['definitions']][link] if link < len(out[n['definitions']]) else None
                    if tgt and tgt == home.get(c): into_home[c] += 1
                elif e.get('has_trader') and not e.get('has_capital'): coll[c] += 1
    res = collections.Counter(); bad = []
    for c, d in cs.items():
        if not isinstance(d, dict) or 'transfer_home_bonus' not in d: continue
        if c not in home: continue
        thb = round(d['transfer_home_bonus'] / 0.1)
        res[('steer', thb == steer[c])] += 1
        res[('steer+coll_away', thb == steer[c] + coll[c])] += 1
        res[('steer_into_home', thb == into_home[c])] += 1
        if thb != steer[c] and len(bad) < 6: bad.append((c, d['transfer_home_bonus'], steer[c], coll[c], into_home[c]))
    return dict(res), bad

if len(sys.argv) > 1 and not sys.argv[1].startswith(('table', 'into')):
  for tag in sys.argv[1:]:
    print(tag, *run(tag))

def table(tag):
    p = [x for x in V.files() if x.stem.endswith(tag)][0]
    ns = V.nodes(p); cs = V.load(p, 'countries')
    steer = collections.Counter(); coll = collections.Counter(); home = {}
    for n in ns:
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('has_capital'): home[c] = n['definitions']
    for n in ns:
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper():
                if e.get('type') and e.get('has_trader'): steer[c] += 1
                elif e.get('has_trader') and not e.get('has_capital'): coll[c] += 1
    t = collections.Counter()
    for c, d in cs.items():
        if isinstance(d, dict) and 'transfer_home_bonus' in d and c in home:
            t[(steer[c], coll[c], round(d['transfer_home_bonus'] / 0.1))] += 1
    return t

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'table':
    t = table(sys.argv[2])
    for k in sorted(t): print('steer', k[0], 'collect_away', k[1], 'thb/0.1', k[2], 'countries', t[k])

def table2(tag):
    p = [x for x in V.files() if x.stem.endswith(tag)][0]
    ns = V.nodes(p); cs = V.load(p, 'countries')
    steer = collections.Counter(); away = collections.Counter(); homec = collections.Counter(); hastrader = set(); home = {}
    for n in ns:
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('has_capital'): home[c] = n['definitions']
    for n in ns:
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('has_trader'):
                if e.get('type'): steer[c] += 1
                elif e.get('has_capital'): homec[c] += 1
                else: away[c] += 1
    t = collections.Counter()
    for c, d in cs.items():
        if isinstance(d, dict) and 'transfer_home_bonus' in d and c in home:
            t[(steer[c], away[c], homec[c], round(d['transfer_home_bonus'] / 0.1))] += 1
    return t

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'table2':
    t = table2(sys.argv[2])
    for k in sorted(t): print('steer', k[0], 'collect_away', k[1], 'collect_home_with_merchant', k[2], 'thb/0.1', k[3], 'countries', t[k])

def into_home_table(tag):
    p = [x for x in V.files() if x.stem.endswith(tag)][0]
    ns = V.nodes(p); names = [n['definitions'] for n in ns]
    out = collections.defaultdict(list)
    for n in ns:
        for inc in as_list(n.get('incoming')):
            if isinstance(inc, dict) and 'from' in inc: out[names[int(inc['from']) - 1]].append(n['definitions'])
    cs = V.load(p, 'countries'); steer = collections.Counter(); away = collections.Counter(); into = collections.Counter(); home = {}
    for n in ns:
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('has_capital'): home[c] = n['definitions']
    for n in ns:
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('has_trader'):
                if e.get('type'):
                    steer[c] += 1
                    link = int(e.get('steer_power', 0)); o = out[n['definitions']]
                    if link < len(o) and o[link] == home.get(c): into[c] += 1
                elif not e.get('has_capital'): away[c] += 1
    t = collections.Counter()
    for c, d in cs.items():
        if isinstance(d, dict) and 'transfer_home_bonus' in d and c in home and steer[c] and not away[c]:
            t[('steerers', steer[c], 'into_home', into[c], 'thb/0.1', round(d['transfer_home_bonus'] / 0.1))] += 1
    return t

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'into':
    for k, v in sorted(into_home_table(sys.argv[2]).items()): print(k, v)
