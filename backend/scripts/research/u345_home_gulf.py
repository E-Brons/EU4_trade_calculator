"""R02 within-country switch: TUR gulf_of_aden steer (U03,U04) -> collect-away (U05) vs sibling steering node crimea; embargoers' own power there."""
import sys; sys.path.insert(0, 'scripts/research')
import u345_home_load as L
def f(x, d=0.0):
    try: return float(x)
    except Exception: return d
for sid in ('S80', 'U03', 'U04', 'U05'):
    ns = {n['definitions']: n for n in L.nodes(sid)}; emb = L.countries(sid)['TUR'].get('trade_embargoed_by') or []
    print("==", sid, "TUR embargoed by", list(emb))
    for nd in ('gulf_of_aden', 'crimea', 'basra', 'alexandria', 'hormuz'):
        n = ns[nd]; e = n['TUR']
        own = {t: round(f(n[t].get('max_pow')) - f(n[t].get('prev')), 1) for t in emb if isinstance(n.get(t), dict)}
        cls = 'collect-away' if 'total' in e else ('steer' if 'type' in e else 'idle')
        print(f"  {nd:13s} {cls:12s} md={e['max_demand']:<6} top_prov[0]={(n.get('top_provinces') or ['-'])[0]:4s} embargoers' own power there: {own}")
    g, c = f(ns['gulf_of_aden']['TUR']['max_demand']), f(ns['crimea']['TUR']['max_demand'])
    print(f"  gulf/crimea = {g/c:.4f}")
