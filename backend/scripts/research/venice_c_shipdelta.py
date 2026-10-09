"""R11: ship_power is inside max_pow with coefficient 1 - move of the 3-barque fleet between ticks (U19->U20 venice->ragusa, U24->U25 ragusa->alexandria)."""
import sys
sys.path.insert(0,'scripts/research')
import venice_load as V, venice_c_lib as L
F=V.files()
def ent(i,node):
    n=[x for x in V.nodes(F[i]) if x['definitions']==node][0]; return n['VEN']
def show(a,b,node):
    ea,eb=ent(a,node),ent(b,node)
    keys=['max_pow','prev','province_power','ship_power','max_demand','val','has_trader']
    print(f"{node:11} U{7+a:02d}->U{7+b:02d}: "+', '.join(f"{k} {ea.get(k)}->{eb.get(k)}" for k in keys))
    d_mp=eb['max_pow']-ea['max_pow']; d_sp=eb.get('ship_power',0)-ea.get('ship_power',0); d_pp=eb.get('province_power',0)-ea.get('province_power',0); d_pv=eb.get('prev',0)-ea.get('prev',0)
    print(f"    d(max_pow)={d_mp:.3f}  d(ship_power)={d_sp:.3f}  d(province_power)={d_pp:.3f}  d(prev)={d_pv:.3f}  residual={d_mp-d_sp-d_pp-d_pv:.3f}")
show(12,13,'venice'); show(12,13,'ragusa')
show(17,18,'ragusa'); show(17,18,'alexandria')
show(25,26,'alexandria')
