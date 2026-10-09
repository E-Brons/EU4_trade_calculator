"""Second pass (regex readers, no parser/cache): max_demand changes only at the 1st; S01 vs U07; home bonus; ship move lag; away halving."""
import sys, collections, re
sys.path.insert(0,'scripts/research')
import venice_c_raw as R
import venice_load as V
F=[p.name for p in V.files()]
T={n:R.trade_entries(R.read(n)) for n in F}
# A. max_demand positional change counts between consecutive saves
print('A. consecutive pairs: changed max_demand entries')
tick_days={'1444_12_01','1445_01_01','1445_02_01','1445_03_01','1445_04_01','1445_05_01','1445_06_01'}
for a,b in zip(F,F[1:]):
    ea,eb=T[a][0],T[b][0]
    ch=sum(1 for k in ea if k in eb and ea[k].get('max_demand')!=eb[k].get('max_demand'))
    tag=b.replace('Venice','').replace('.eu4','')
    print(f"  {a[6:-4]} -> {tag}: {ch}  {'(next day is a 1st)' if tag in tick_days else ''}")
