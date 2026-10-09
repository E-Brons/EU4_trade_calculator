"""R11: Venice's fleets and the ship terms in the trade entries across the series."""
import sys, json, collections
sys.path.insert(0,'scripts/research')
import venice_load as V, venice_c_lib as L
for i,p in enumerate(V.files()):
    c=V.load(p,'countries')['VEN']; ns=V.nodes(p)
    fl=[]
    for f in L.as_list(c.get('navy')):
        if not isinstance(f,dict): continue
        types=collections.Counter(s.get('type') for s in L.as_list(f.get('ship')) if isinstance(s,dict))
        fl.append((f.get('name'),f.get('location'),dict(types),f.get('mission') or f.get('trade'),f.get('on_my_way'),bool(f.get('leader')),[k for k in f if k not in('id','name','location','ship','base','movement_progress','previous','leader')][:8]))
    ent={n['definitions']:{k:v for k,v in n['VEN'].items() if k in('ship_power','light_ship','max_pow','prev','val','has_trader')} for n in ns if isinstance(n.get('VEN'),dict) and ('ship_power' in n['VEN'] or 'light_ship' in n['VEN'])}
    if i in (0,1,3,7,13,19,20,21,22,23) or True:
        print(f"U{7+i:02d} {p.stem[6:]} protect={c.get('num_ships_protecting_trade')} ent={ent}")
        if i in (0,3,20,23): print('    fleets:',fl)
