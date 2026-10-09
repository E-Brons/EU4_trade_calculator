"""Verifier (independent): is max_demand at a top-province node equal to the home-node value or to the foreign value?"""
import sys, pickle, collections
sys.path.insert(0, 'scripts/research')
import common
C = collections.Counter(); diff_both = []
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    for tag, c in m['countries'].items():
        if c.get('trade_embargoed_by'): continue
        home = c.get('home_node'); hv = None; tops = []; fors = []
        for n in m['nodes']:
            t = n.get(tag)
            if not isinstance(t, dict) or 'max_demand' not in t: continue
            if 'total' in t and not t.get('has_capital'): continue
            top = n.get('top_provinces') or []
            if n['definitions'] == home: hv = t['max_demand']
            elif top and top[0] == tag: tops.append(t['max_demand'])
            else: fors.append(t['max_demand'])
        if hv is None or not tops or not fors: continue
        fv = collections.Counter(fors).most_common(1)[0][0]
        tv = collections.Counter(tops).most_common(1)[0][0]
        C['total'] += 1
        eh, ef = abs(tv - hv) <= 0.0015, abs(tv - fv) <= 0.0015
        C['top==home&&top!=foreign' if eh and not ef else 'top==foreign&&top!=home' if ef and not eh else 'top==both' if eh and ef else 'top differs from both'] += 1
        if not eh and not ef: diff_both.append((e['id'], tag, hv, tv, fv))
        C['home>foreign' if hv > fv + .0015 else 'home<foreign' if hv < fv - .0015 else 'home==foreign'] += 1
print(dict(C)); print(collections.Counter(x[1] for x in diff_both), collections.Counter(x[0] for x in diff_both))
