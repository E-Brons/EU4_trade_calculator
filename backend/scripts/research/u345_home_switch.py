"""Natural experiments between consecutive saves: countries whose action/merchant status at a node changed; show md/X before and after."""
import sys, collections; sys.path.insert(0, 'scripts/research')
import u345_home_load as L
def f(x, d=None):
    try: return float(x)
    except Exception: return d
def cls(e):
    if 'has_capital' in e: return 'HOME+' + ('M' if e.get('has_trader') else '-') + ('c' if 'total' in e else '')
    if 'total' in e: return 'AWAY-collect'
    if 'type' in e: return 'STEER'
    return 'idle-M' if e.get('has_trader') else 'passive'
def table(sid):
    t = {}
    for n in L.nodes(sid):
        for tag, e in n.items():
            if isinstance(e, dict) and 'max_demand' in e and 'max_pow' in e:
                X = f(e['money']) / f(e['total']) - 1 if 'total' in e and f(e['total'], 0) >= 3 else None
                t[(n['definitions'], tag)] = (cls(e), f(e['max_demand']), X, bool(e.get('has_trader')))
    return t
for a, b in [('S80', 'U03'), ('U03', 'U04'), ('U04', 'U05')]:
    A, B = table(a), table(b); ch = []
    for k in A.keys() & B.keys():
        (ca, ma, xa, _), (cb, mb, xb, _) = A[k], B[k]
        if ca != cb and {ca[:4], cb[:4]} != {'pass'} and (ca.startswith('HOME') or cb.startswith('HOME') or 'collect' in ca or 'collect' in cb or ca == 'STEER' or cb == 'STEER'):
            ch.append((k[1], k[0], ca, cb, ma, mb, None if xa is None else round(xa, 3), None if xb is None else round(xb, 3)))
    ch.sort()
    print(f"=== {a} -> {b}: {len(ch)} node/tag entries whose class changed")
    for c in ch: print("  %-4s %-16s %-14s -> %-14s md %-6s -> %-6s X %s -> %s" % c)
