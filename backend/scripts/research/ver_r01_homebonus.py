"""Verifier (independent): home-node bonus. For non-embargoed countries with home entry, top node, steering merchants: compare top-home with 0.1*m."""
import sys, pickle, collections
sys.path.insert(0, 'scripts/research')
import common
rows = []; C = collections.Counter()
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    for tag, c in m['countries'].items():
        if c.get('trade_embargoed_by'): continue
        home = c.get('home_node'); hv = None; tops = []; fors = []; steer = 0; awaycol = 0
        for n in m['nodes']:
            t = n.get(tag)
            if not isinstance(t, dict): continue
            if t.get('has_trader') and 'type' in t: steer += 1
            if 'total' in t and not t.get('has_capital'): awaycol += 1; continue
            if 'max_demand' not in t: continue
            top = n.get('top_provinces') or []
            if n['definitions'] == home: hv = t['max_demand']
            elif top and top[0] == tag: tops.append(t['max_demand'])
            else: fors.append(t['max_demand'])
        if hv is None or not tops or not fors or steer == 0: continue
        tv = collections.Counter(tops).most_common(1)[0][0]
        key = ('ticked' if e['kind'] == 'ticked' or e['id'] in ('S79','S80','U01','U02') else 'start', 'awaycollector' if awaycol else 'noaway')
        C[key + ('top-home==0.1m' if abs(tv - hv - 0.1 * steer) < 0.0025 else 'home-top==0.1m' if abs(hv - tv - 0.1 * steer) < 0.0025 else 'top==home' if abs(tv - hv) < 0.0015 else 'other',)] += 1
        if key[0] == 'ticked': rows.append((e['id'], tag, steer, awaycol, hv, tv, collections.Counter(fors).most_common(1)[0][0]))
for k, v in sorted(C.items()): print(v, k)
for r in rows: print(r)
