"""R07: within-country change of home X between consecutive saves vs changes in home-merchant presence, estate loyalty >= thresholds, dip tech, idea levels, reforms."""
import sys, collections; sys.path.insert(0, 'scripts/research')
import u345_home_load as L
def f(x, d=None):
    try: return float(x)
    except Exception: return d
def snap(sid):
    cs = L.countries(sid); out = {}
    for n in L.nodes(sid):
        for tag, e in n.items():
            if isinstance(e, dict) and 'has_capital' in e and 'total' in e and f(e['total'], 0) >= 3 and tag in cs:
                c = cs[tag]; est = c.get('estate') or []
                est = est if isinstance(est, list) else [est]
                loy = [f(x.get('loyalty')) for x in est if isinstance(x, dict)]
                out[tag] = dict(X=round(f(e['money']) / f(e['total']) - 1, 2), M=bool(e.get('has_trader')), n60=sum(1 for l in loy if l is not None and l >= 60),
                                loy=[round(l) for l in loy if l is not None], dip=(c.get('technology') or {}).get('dip_tech'),
                                ideas=tuple(sorted((c.get('active_idea_groups') or {}).items())),
                                reforms=tuple((c.get('government') or {}).get('reform_stack', {}).get('reforms', [])),
                                mods=tuple(sorted(str(m.get('modifier')) for m in (c.get('modifier') if isinstance(c.get('modifier'), list) else [c.get('modifier')] if c.get('modifier') else []) if isinstance(m, dict))))
    return out
for a, b in [('S79', 'S80'), ('S80', 'U03'), ('U03', 'U04'), ('U04', 'U05')]:
    A, B = snap(a), snap(b); rows = []
    for t in sorted(A.keys() & B.keys()):
        x, y = A[t], B[t]; dX = round(y['X'] - x['X'], 2)
        rows.append((t, dX, int(y['M']) - int(x['M']), y['n60'] - x['n60'], (y['dip'] or 0) - (x['dip'] or 0), x['ideas'] != y['ideas'], x['reforms'] != y['reforms'], x['mods'] != y['mods']))
    unchanged = [r for r in rows if r[2] == 0 and r[3] == 0 and r[4] == 0 and not r[5] and not r[6]]
    print(f"=== {a}->{b}: countries with home X in both {len(rows)}; dX histogram {dict(collections.Counter(r[1] for r in rows))}")
    print("    no change in merchant/n60/dip/ideas/reforms:", len(unchanged), "dX hist", dict(collections.Counter(r[1] for r in unchanged)))
    print("    merchant-at-home changed:", [(r[0], 'dX', r[1], 'dM', r[2], 'dn60', r[3], 'dDip', r[4], 'ideas', r[5], 'reforms', r[6], 'mods', r[7]) for r in rows if r[2] != 0])
    print("    n60 changed, merchant same:", [(r[0], r[1], 'dn60', r[3], 'dDip', r[4]) for r in rows if r[2] == 0 and r[3] != 0 and r[4] == 0 and not r[5] and not r[6]])

print("\n--- strict subset: nothing changed (merchant, n60, dip, ideas, reforms, modifier names) ---")
for a, b in [('U03', 'U04'), ('U04', 'U05')]:
    A, B = snap(a), snap(b); same = [t for t in A.keys() & B.keys() if A[t]['M'] == B[t]['M'] and A[t]['ideas'] == B[t]['ideas'] and A[t]['reforms'] == B[t]['reforms'] and A[t]['mods'] == B[t]['mods'] and (A[t]['dip'] == B[t]['dip'])]
    print(a, '->', b, len(same), 'countries; dX hist', dict(collections.Counter(round(B[t]['X'] - A[t]['X'], 2) for t in same)), '; nonzero:', [(t, round(B[t]['X'] - A[t]['X'], 2)) for t in same if abs(B[t]['X'] - A[t]['X']) > 0.001])
for t, (a, b) in {'TUR': ('U04', 'U05'), 'YEM': ('U04', 'U05')}.items():
    A, B = snap(a)[t], snap(b)[t]
    print(t, a, '->', b, 'modifier names added', sorted(set(B['mods']) - set(A['mods'])), 'removed', sorted(set(A['mods']) - set(B['mods'])), 'X', A['X'], '->', B['X'])
