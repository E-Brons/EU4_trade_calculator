"""Second pass C/D/F/H with regex readers only: home bonus, embargo timing, ship term lag and max_pow identity, home X."""
import sys, re, collections
sys.path.insert(0,'scripts/research')
import venice_c_raw as R
import venice_load as V
F=[p.name for p in V.files()]
TX={n:R.read(n) for n in F}
TE={n:R.trade_entries(TX[n]) for n in F}
def lab(n): return n[6:-4]
print('C. VEN home node: md@venice, transfer_home_bonus (country), steering entries')
for n in F:
    e=TE[n][0]; seg=R.country_segment(TX[n],'VEN')
    v=e[('venice','VEN')]
    steer=[nd for (nd,t),x in e.items() if t=='VEN' and x.get('has_trader') and 'type' in x]
    print(f"  {lab(n)} md={v['max_demand']} bonus={R.scalar(seg,'transfer_home_bonus')} steerers={len(steer)} X={v['money']/v['total']:.4f}")
print('F. 2nd Fleet mission node vs ship entry location')
for n in F:
    seg=R.country_segment(TX[n],'VEN')
    node=None
    for m in re.finditer(r"\n\t\tnavy=\{", seg):
        blk=R._balanced(seg,m.end()-1)
        if 'name="2nd Fleet"' in blk:
            mm=re.search(r"protect_mission=\{[^}]*?\bnode=(\d+)",blk,re.S)
            node=int(mm.group(1)) if mm else None
    e=TE[n][0]
    ent=[(nd,x['ship_power'],x['max_pow']) for (nd,t),x in e.items() if t=='VEN' and 'ship_power' in x]
    print(f"  {lab(n)} mission_node_index={node} ship entry={ent}")
