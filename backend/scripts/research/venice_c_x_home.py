"""Venice's income efficiency at the home node venice (money/total) across the series, with ships/merchants/bonus state."""
import sys
sys.path.insert(0,'scripts/research')
import venice_load as V
for i,p in enumerate(V.files()):
    ns=V.nodes(p); c=V.load(p,'countries')['VEN']
    e=[n for n in ns if n['definitions']=='venice'][0]['VEN']
    x=e['money']/e['total']
    print(f"U{7+i:02d} {p.stem[6:]:>10} money={e['money']:.3f} total={e['total']:.3f} X={x:.4f} ship_power={e.get('ship_power')} pf={e.get('power_fraction')} md={e['max_demand']} bonus={c.get('transfer_home_bonus')} merchants_steering={[n['definitions'] for n in ns if isinstance(n.get('VEN'),dict) and n['VEN'].get('has_trader')]} trade_mission={c.get('trade_mission')}")
