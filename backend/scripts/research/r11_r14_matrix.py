"""R14 Q1/Q2: check the draft's matrix against the saves: tag exists, home node (has_capital), merchants, role/max_demand at the named node, node links."""
import sys,json; sys.path.insert(0,'scripts/research')
import common
from common import as_list
tn=json.load(open('data/tradenodes.json'))['nodes']
E={x['id']:x for x in common.entries()}
def env(c):
    m=c.get('merchants'); 
    if not isinstance(m,dict): return []
    return as_list(m.get('envoy'))
CASES=[('IV-01','S03','FRA','english_channel'),('IV-14','S03','FRA','champagne'),('IV-08','S03','FRA','north_sea'),
 ('IV-02','S02','ENG','genua'),('IV-09','S02','ENG','english_channel'),('IV-12','S02','ENG','lubeck'),
 ('IV-03','S04','CAS','tunis'),('IV-10','S04','CAS','bordeaux'),('IV-04','S14','TUR','alexandria'),
 ('IV-05/06/11','S05','POR','safi'),('IV-11','S05','POR','sevilla'),('IV-17','S05','POR','ivory_coast'),('IV-07','S06','HAB','wien')]
for iv,sid,tag,node in CASES:
    e=E[sid]; nodes=common.nodes(e); N={n['definitions']:n for n in nodes}
    cs=common.block(e,'countries'); c=cs.get(tag)
    home=[n['definitions'] for n in nodes if isinstance(n.get(tag),dict) and n[tag].get('has_capital')]
    placed=[(n['definitions'],'steer' if 'type' in n[tag] else ('collect' if ('total' in n[tag]) else 'present')) for n in nodes if isinstance(n.get(tag),dict) and n[tag].get('has_trader')]
    ent=(N[node].get(tag) if isinstance(N[node].get(tag),dict) else None)
    print(f"{iv} {sid} {tag} date {e['date']} | home(has_capital)={home} | envoys={len(env(c))} placed={placed}")
    print(f"     node {node}: links={[o['target'] for o in tn[node]['outgoing']]} inland={tn[node]['inland']} | {tag} entry: " + (json.dumps({k:ent.get(k) for k in ('province_power','prev','max_pow','max_demand','val','has_trader','has_capital','type','steer_power','total','ship_power','light_ship')},default=str) if ent else 'none') )
    print(f"     {tag} max_demand at node (stub or entry):", (N[node].get(tag) or {}).get('max_demand') if isinstance(N[node].get(tag),dict) else None, '| trade_port', c.get('trade_port'))

print('--- tag existence / home node')
def exists(c): 
    return isinstance(c,dict) and (c.get('num_of_cities',0) or 0)>0
for sid in ('S03','S06','S62'):
    e=E[sid]; nodes=common.nodes(e); cs=common.block(e,'countries')
    for tag in ('PRU','BRA','SCO','ARA','OPM','CAS','HAB'):
        c=cs.get(tag)
        home=[n['definitions'] for n in nodes if isinstance(n.get(tag),dict) and n[tag].get('has_capital')]
        print(sid,e['date'],tag,'in countries block:',c is not None,'num_of_cities',(c or {}).get('num_of_cities'),'home',home,'envoys',len(env(c)) if c else None,'placed',[(n['definitions'],'steer' if 'type' in n[tag] else 'collect' if 'total' in n[tag] else 'present') for n in nodes if isinstance(n.get(tag),dict) and n[tag].get('has_trader')] if c else None)
