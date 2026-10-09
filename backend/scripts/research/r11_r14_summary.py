"""R11 summary numbers: ship entries per save; U-saves vs S-saves; uniqueness of the subset fit; factor histogram per entry."""
import sys,pickle,json; sys.path.insert(0,'scripts/research')
exec(open('scripts/research/r11_r14_fleetflags.py').read().split("unique=0")[0])
ents={}
for e in common.entries():
    c=0; d={}
    for n in common.nodes(e):
        for tag,x in n.items():
            if isinstance(x,dict) and 'light_ship' in x: c+=1; d[(n['definitions'],tag)]=(x['light_ship'],x['ship_power'])
    ents[e['id']]=d
print('saves with any light_ship entry:',{k:len(v) for k,v in ents.items() if v})
print('start snapshots with ship entries:',sum(1 for k,v in ents.items() if v and k not in('S79','S80','U01','U02')))
print('U02==S79 ship entries:',ents['U02']==ents['S79'],' U01==S80:',ents['U01']==ents['S80'])
# fit statistics on entries
tot=0; uniq=0; hist=Counter(); amb=[]
for sid,key,en,lst,sols in rows:
    if en is None: continue
    tot+=1
    if len(sols)==1:
        uniq+=1; base=sum(lst[i]['base'] for i in sols[0]); hist[round(en[1]/base,4)]+=1
    else: amb.append((sid,key,en,len(sols)))
print('entries',tot,'unique subset fit',uniq,'ambiguous',amb); print('factor histogram per entry',dict(hist))
# types per country with fleets (all fleets not only protect): total light ships owned vs on protect, for TUR
for sid in ('S79','S80'):
    e=[x for x in common.entries() if x['id']==sid][0]
    c=common.block(e,'countries')['TUR']; nv=c['navy']; tot=Counter()
    for f in nv:
        for s in (f['ship'] if isinstance(f['ship'],list) else [f['ship']]): tot[s['type']]+=1
    print(sid,'TUR ships by type (all fleets):',dict(tot))
