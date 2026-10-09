"""R01 Q1: per-row table for TUR (S79) rows below the cap, with embargoers' power at the node."""
import sys, os, re, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
m = pickle.loads((common.CACHE / "master_S79.pkl").read_bytes())
emb = m['countries']['TUR']['trade_embargoed_by']; home = m['countries']['TUR']['home_node']
print('embargoed by', emb, 'home', home, 'transfer from', m['countries']['TUR'].get('transfer_trade_power_from'))
CAP_F, CAP_D = 2.11, 1.895
hdr = ('node','class','md','cap','red%','X(P/(S+5NH))','0.5*X%','  embargoers (prov+ship | prev)')
print(hdr)
for n in m['nodes']:
    v = n.get('TUR')
    if not (isinstance(v, dict) and 'val' in v): continue
    ents = {k: x for k, x in n.items() if TAG.match(k) and isinstance(x, dict)}
    S = sum(x.get('ship_power', 0) + x.get('province_power', 0) for x in ents.values()); nh = sum(1 for x in ents.values() if x.get('has_capital'))
    away = 'total' in v and not v.get('has_capital')
    dom = n['definitions'] == home or (n.get('top_provinces') or [None])[0] == 'TUR'
    cap = (CAP_D if dom else CAP_F) * (0.5 if away else 1)
    X = sum((ents[q].get('ship_power', 0) + ents[q].get('province_power', 0)) / (S + 5 * nh) for q in emb if q in ents)
    red = 1 - v['max_demand'] / cap
    det = ' '.join(f"{q}:{ents[q].get('province_power',0)+ents[q].get('ship_power',0):.1f}|{ents[q].get('prev',0):.1f}" for q in emb if q in ents and 'val' in ents[q])
    print(f"{n['definitions']:16s} {'dom' if dom else 'for'}{'/away' if away else ''}  {v['max_demand']:.3f} {cap:.3f} {100*red:6.2f} {X:.4f} {50*X:6.2f}  {det}")
