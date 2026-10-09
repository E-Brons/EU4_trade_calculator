"""Verifier (independent): R02 away-collection factor and steering/merchant-without-action rows (non-embargoed countries)."""
import sys, pickle, collections
sys.path.insert(0, 'scripts/research')
import common
C = collections.Counter(); off = []
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    for tag, c in m['countries'].items():
        if c.get('trade_embargoed_by') or tag == 'PIR': continue
        home = c.get('home_node'); rows = []
        for n in m['nodes']:
            t = n.get(tag)
            if not isinstance(t, dict) or 'max_demand' not in t: continue
            top = n.get('top_provinces') or []
            cls = 'dom' if (n['definitions'] == home or (top and top[0] == tag)) else 'for'
            kind = ('home' if t.get('has_capital') else 'collect-away' if 'total' in t else 'steer-away' if (t.get('has_trader') and 'type' in t) else 'merchant-noaction' if t.get('has_trader') else 'passive')
            rows.append((n['definitions'], cls, kind, t['max_demand']))
        base = {}
        for cls in ('dom', 'for'):
            v = [r[3] for r in rows if r[1] == cls and r[2] == 'passive']
            if v: base[cls] = collections.Counter(v).most_common(1)[0][0]
        for nid, cls, kind, md in rows:
            if kind in ('collect-away', 'steer-away', 'merchant-noaction') and cls in base:
                r = md / base[cls]
                k = 'ratio 0.5' if abs(r - 0.5) <= 0.003 else 'ratio 1' if abs(r - 1) <= 0.003 else 'other'
                C[(kind, k)] += 1
                if k == 'other': off.append((e['id'], tag, nid, kind, md, base[cls]))
            elif kind in ('collect-away',): C[('collect-away', 'no same-class passive baseline')] += 1
for k, v in sorted(C.items()): print(v, k)
print(len(off), off[:12])
