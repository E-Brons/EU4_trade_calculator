"""R02/R06/R07: merchant entries in the pre-tick snapshot (U07-U09, before the first 1st) vs after it (U10): has_trader without `type` = collecting."""
import sys, collections
sys.path.insert(0,'scripts/research')
import venice_c_raw as R, venice_load as V
F=[p.name for p in V.files()]
def coll(name):
    e,_=R.trade_entries(R.read(name))
    out={}
    for (nd,t),v in e.items():
        if v.get('has_trader') and 'type' not in v: out[(nd,t)]=v
    return out
c7,c9,c10=coll(F[0]),coll(F[2]),coll(F[3])
print('collecting merchant entries (has_trader, no type): U07',len(c7),'U09',len(c9),'U10',len(c10))
away7={k for k,v in c7.items() if not v.get('has_capital')}; away10={k for k,v in c10.items() if not v.get('has_capital')}
print('away (not has_capital): U07',len(away7),'with money',sum(1 for k in away7 if 'money' in c7[k]),'| U10',len(away10),'with money',sum(1 for k in away10 if 'money' in c10[k]))
print('U07 away entries still an away collector in U10:',len(away7&away10),'of',len(away7))
# md halving: ratio md(U10)/md(U09) for those
e9,_=R.trade_entries(R.read(F[2])); e10,_=R.trade_entries(R.read(F[3]))
ratios=collections.Counter()
for k in away7&away10:
    a,b=e9[k].get('max_demand'),e10[k].get('max_demand')
    ratios[round(b/a,2)]+=1
print('max_demand U10/U09 for those:',ratios.most_common(6))
# max_pow change (+2 merchant) 
d=collections.Counter()
for k in away7&away10:
    a,b=e9[k].get('max_pow'),e10[k].get('max_pow')
    if a is not None and b is not None: d[round(b-a,1)]+=1
print('max_pow U10-U09 for those (rounded 0.1):',d.most_common(6))
# home collectors
home7={k for k,v in c7.items() if v.get('has_capital')}
print('home collectors with merchant: U07',len(home7),'with money',sum(1 for k in home7 if 'money' in c7[k]))
