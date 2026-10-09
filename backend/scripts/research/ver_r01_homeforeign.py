"""Verifier (independent): home-node max_demand vs foreign value for non-embargoed countries (R01 C-04)."""
import sys, pickle, collections
sys.path.insert(0, 'scripts/research')
import common
C = collections.Counter(); ratios = []
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    for tag, c in m['countries'].items():
        if c.get('trade_embargoed_by') or tag == 'PIR': continue
        home = c.get('home_node'); hv = None; fors = []
        for n in m['nodes']:
            t = n.get(tag)
            if not isinstance(t, dict) or 'max_demand' not in t: continue
            top = n.get('top_provinces') or []
            if n['definitions'] == home: hv = t['max_demand']; continue
            if top and top[0] == tag: continue
            if 'total' in t and not t.get('has_capital'): continue
            fors.append(t['max_demand'])
        if hv is None or not fors: continue
        fv = collections.Counter(fors).most_common(1)[0][0]
        C['home<foreign' if hv < fv - 0.0005 else 'home>foreign' if hv > fv + 0.0005 else 'equal'] += 1
        ratios.append(hv / fv)
print(dict(C), sum(C.values()), 'ratio min/median/max', round(min(ratios), 3), round(sorted(ratios)[len(ratios)//2], 3), round(max(ratios), 3))
