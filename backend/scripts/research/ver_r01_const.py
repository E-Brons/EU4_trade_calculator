"""Verifier (independent): spread of a non-embargoed country's max_demand over nodes that are neither home, top-province nor away-collecting."""
import sys, pickle, collections
sys.path.insert(0, 'scripts/research')
import common
nd = collections.Counter(); spread2 = collections.Counter(); big = []
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    for tag, c in m['countries'].items():
        if c.get('trade_embargoed_by'): continue
        home = c.get('home_node'); vals = []
        for n in m['nodes']:
            t = n.get(tag)
            if not isinstance(t, dict) or 'max_demand' not in t: continue
            top = n.get('top_provinces') or []
            if n['definitions'] == home or (top and top[0] == tag): continue
            if 'total' in t and not t.get('has_capital'): continue
            vals.append(t['max_demand'])
        if not vals: continue
        d = len(set(vals)); nd[d] += 1
        sp = round(max(vals) - min(vals), 3)
        if d == 2: spread2[sp] += 1
        if sp > 0.002: big.append((e['id'], tag, sp, sorted(set(vals))[:4]))
print('groups', sum(nd.values()), dict(sorted(nd.items())))
print('two-valued spread', dict(sorted(spread2.items())))
print('spread>0.002:', len(big), big[:8])
