"""Q1/Q2: TUR actions, md, extras, X at every TUR node with data, across S79,S80,U03,U04,U05 (own code)."""
import sys; sys.path.insert(0, 'scripts/research')
import u345_home_load as L
def f(x, d=None):
    try: return float(x)
    except Exception: return d
def mods(e):
    m = e.get('modifier'); 
    if m is None: return []
    return m if isinstance(m, list) else [m]
def cls(e):
    if 'has_capital' in e: return 'HOME'
    if 'total' in e: return 'COLLECT-AWAY'
    if 'type' in e: return 'STEER'
    if e.get('has_trader'): return 'merchant-idle'
    return 'passive'
for sid in L.IDS:
    ns = L.nodes(sid); c = L.countries(sid)['TUR']
    print(f"=== {sid} date={L.gamestate(sid)[:40].split()[0] if False else ''}")
    merch = 0; rows = []
    for n in ns:
        e = n.get('TUR')
        if not isinstance(e, dict) or 'max_pow' not in e: continue
        if not (e.get('has_trader') or 'type' in e or 'total' in e or 'has_capital' in e or f(e.get('light_ship'), 0)): continue
        pp, sp, pv, mp = f(e.get('province_power'), 0), f(e.get('ship_power'), 0), f(e.get('prev'), 0), f(e['max_pow'])
        ext = round(mp - pp - sp - pv, 3)
        modp = sum(f(m.get('power'), 0) for m in mods(e))
        R = round(ext - 5 * ('has_capital' in e) - modp, 3)
        X = round(f(e['money']) / f(e['total']) - 1, 3) if 'total' in e and f(e.get('total'), 0) > 0 else None
        if e.get('has_trader'): merch += 1
        rows.append((n['definitions'], cls(e), bool(e.get('has_trader')), f(e['max_demand']), ext, R, X, int(f(e.get('light_ship'), 0))))
    print(f"TUR merchants in trade entries: {merch}; trade_port={c.get('trade_port')}")
    for r in rows: print("  %-14s %-13s trader=%-5s md=%-6s extras=%-7s R=%-6s X=%-6s ships=%s" % r)
