"""R11: 2nd Fleet (3 barques): mission node / route target / on_my_way vs the node where the trade entry carries the ship term, per save."""
import sys
sys.path.insert(0,'scripts/research')
import venice_load as V, venice_c_lib as L
for i,p in enumerate(V.files()):
    c=V.load(p,'countries')['VEN']; ns=V.nodes(p); names=[n['definitions'] for n in ns]
    f2=[f for f in L.as_list(c.get('navy')) if isinstance(f,dict) and f.get('name')=='2nd Fleet'][0]
    m=(f2.get('mission') or {}).get('protect_mission') if isinstance(f2.get('mission'),dict) else None
    where=[n['definitions'] for n in ns if isinstance(n.get('VEN'),dict) and 'light_ship' in n['VEN']]
    print(f"U{7+i:02d} {p.stem[6:]:>10} loc={f2.get('location')} mission_node={(m or {}).get('node')}({names[(m['node']-1)] if m else None}) target={(m or {}).get('current_route_target')} on_my_way={(m or {}).get('on_my_way')} route={(m or {}).get('trade')} entry_at={where} path={f2.get('path')} movement_locked={f2.get('movement_locked')}")
