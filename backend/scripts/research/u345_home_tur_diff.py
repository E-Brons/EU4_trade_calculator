"""Q4: what changed in countries.TUR between consecutive ticked saves (modifiers, ideas, reforms, techs, embargoes, merchants)."""
import sys; sys.path.insert(0, 'scripts/research')
import u345_home_load as L
TAG = sys.argv[1] if len(sys.argv) > 1 else 'TUR'
KEYS = ['modifier', 'flags', 'government', 'active_idea_groups', 'technology', 'institutions', 'mercantilism', 'estate', 'ideas',
        'trade_embargoed_by', 'trade_embargoes', 'merchants', 'num_ships_protecting_trade', 'transfer_trade_power_from',
        'transfer_trade_power_to', 'government_rank', 'current_power_projection', 'prestige', 'navy_tradition', 'development']
def flat(x, p=''):
    out = {}
    if isinstance(x, dict):
        for k, v in x.items(): out.update(flat(v, f"{p}.{k}" if p else str(k)))
    elif isinstance(x, list):
        if x and all(isinstance(i, dict) for i in x):
            for i, v in enumerate(x): out.update(flat(v, f"{p}[{v.get('key', i)}]" if isinstance(v, dict) and 'key' in v else f"{p}[{i}]"))
        else: out[p] = tuple(map(str, x))
    else: out[p] = x
    return out
tur = {s: {k: flat(L.countries(s)[TAG].get(k), k) for k in KEYS if k in L.countries(s)[TAG]} for s in L.IDS}
flats = {s: {kk: vv for k, d in tur[s].items() for kk, vv in d.items()} for s in L.IDS}
PAIRS = [tuple(x.split('-')) for x in sys.argv[2:]] or [('S80', 'U03'), ('U03', 'U04'), ('U04', 'U05')]
for a, b in PAIRS:
    A, B = flats[a], flats[b]; ch = []
    for k in sorted(set(A) | set(B)):
        if A.get(k) != B.get(k):
            if k.startswith(('technology', 'development', 'prestige', 'current_power', 'navy_trad')) and isinstance(B.get(k), float): ch.append((k, A.get(k), B.get(k)))
            else: ch.append((k, A.get(k), B.get(k)))
    print(f"=== {a} -> {b}: {len(ch)} changed fields")
    for c in ch[:60]: print("  ", c)
