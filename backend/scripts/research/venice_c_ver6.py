"""Second pass R11 (regex readers): max_pow change at the two nodes of a fleet move == ship_power change + province_power change + prev change."""
import sys
sys.path.insert(0,'scripts/research')
import venice_c_raw as R, venice_load as V
F=[p.name for p in V.files()]
def ent(i,node): return R.trade_entries(R.read(F[i]))[0][(node,'VEN')]
for a,b,node in ((12,13,'venice'),(12,13,'ragusa'),(17,18,'ragusa'),(17,18,'alexandria')):
    ea,eb=ent(a,node),ent(b,node)
    d=lambda k: (eb.get(k,0.0)-ea.get(k,0.0))
    print(f"{node:10} {F[a][6:-4]}->{F[b][6:-4]}: d max_pow {d('max_pow'):+.3f} = d ship_power {d('ship_power'):+.3f} + d province_power {d('province_power'):+.3f} + d prev {d('prev'):+.3f}; residual {d('max_pow')-d('ship_power')-d('province_power')-d('prev'):+.3f}")
