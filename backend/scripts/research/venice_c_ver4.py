"""Second pass D/E/G with regex readers only: embargo timing, away halving, total-sum(val) identity."""
import sys, re, collections
sys.path.insert(0,'scripts/research')
import venice_c_raw as R
import venice_load as V
F=[p.name for p in V.files()]
TX={n:R.read(n) for n in F}
TE={n:R.trade_entries(TX[n]) for n in F}
def lab(n): return n[6:-4]

print('D. embargo field vs max_demand of the embargoed country at a node where the embargoer has power')
def emb_pairs(text):
    out=[]
    for m in re.finditer(r"\n\t([A-Z][A-Z0-9]{2})=\{\n", text[text.index("\ncountries={\n"):]):
        pass
    return out
def embargoed(text, tag):
    seg=R.country_segment(text,tag)
    m=re.search(r"\n\t\ttrade_embargoed_by=\{\n\t\t\t([^\n]*)\n", seg)
    return m.group(1).split() if m else []
rows=[]
for n in F:
    e=TE[n][0]
    lan=embargoed(TX[n],'LAN'); gen=embargoed(TX[n],'GEN'); eng=embargoed(TX[n],'ENG')
    cr=e.get(('crimea','LAN'),{}).get('max_demand'); cn=e.get(('champagne','ENG'),{}).get('max_demand'); ga=e.get(('alexandria','GEN'),{}).get('max_demand')
    print(f"  {lab(n)}: LAN embargoed_by={lan} GEN by={gen} ENG by={eng} | LAN@crimea={cr} GEN@alexandria={ga} ENG@champagne={cn}")

print('G. total - sum(val) vs p_pow - sum(province_power)')
bad=0; nn=0
for n in F:
    e,nodes=TE[n]
    by=collections.defaultdict(list)
    for (nd,t),v in e.items(): by[nd].append(v)
    for nd,nf in nodes.items():
        if 'total' not in nf: continue
        nn+=1
        sv=sum(v.get('val',0) for v in by[nd]); sp=sum(v.get('province_power',0) for v in by[nd])
        if abs((nf['total']-sv)-(nf.get('p_pow',sp)-sp))>0.0035: bad+=1
print('  node instances',nn,'mismatching',bad)

print('E. away collectors: has_trader, no type, money present, not has_capital')
tot=ok=0
for n in F:
    e,nodes=TE[n]
    cls=collections.defaultdict(collections.Counter); dom={}
    for (nd,t),v in e.items():
        if 'max_demand' in v and t!='PIR':
            cls[t][v['max_demand']]+=1
    for (nd,t),v in e.items():
        if v.get('has_trader') and 'type' not in v and 'money' in v and not v.get('has_capital'):
            # candidates: foreign-class mode or the country's top-node class; accept if md*2 equals any class value of that country (+-0.0011)
            tot+=1
            if any(abs(v['max_demand']*2-c)<=0.0022 for c in cls[t]): ok+=1
print('  away-collector entries',tot,'with md*2 == one of the country\'s own class values:',ok)
