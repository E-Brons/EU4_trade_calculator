import sys, os, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
rows=[]
for e in common.entries():
    for n in common.nodes(e):
        ents={k:v for k,v in n.items() if TAG.match(k) and isinstance(v,dict)}
        sv=sum(v.get('val',0) for v in ents.values())
        rows.append(dict(save=e['id'],node=n['definitions'],total=n.get('total'),sv=sv,gap=(n.get('total') or 0)-sv,
            nc=n.get('num_collectors'),ncp=n.get('num_collectors_including_pirates'),cp=n.get('collector_power'),cpp=n.get('collector_power_including_pirates'),
            rp=n.get('retain_power'),pir='PIR' in ents,pirent=ents.get('PIR'),nents=len(ents), ents=ents, n=n))
print('node instances', len(rows))
print('has total key', sum(r['total'] is not None for r in rows))
g=[r for r in rows if r['total'] is not None]
print('gap>0.01:', sum(abs(r['gap'])>0.01 for r in g), ' gap>2%:', sum(abs(r['gap'])>0.02*r['total'] for r in g), ' gap<-0.01:', sum(r['gap']<-0.01 for r in g))
print('gap in (0.001..0.01]', sum(0.0015<abs(r['gap'])<=0.01 for r in g))
# PIR entry
print('PIR present', sum(r['pir'] for r in rows))
print('PIR entry key sets', collections.Counter(tuple(sorted(r['pirent'])) for r in rows if r['pir']))
# num_collectors vs including pirates
d=collections.Counter((r['ncp']-r['nc']) if r['nc'] is not None and r['ncp'] is not None else None for r in rows); print('ncp-nc',d)
d=collections.Counter((r['pir'], (r['ncp']-r['nc']) if r['nc'] is not None and r['ncp'] is not None else None) for r in rows); print('(PIR present, ncp-nc)',d)
d=collections.Counter(round(r['cpp']-r['cp'],3) if r['cp'] is not None and r['cpp'] is not None else None for r in rows); print('cpp-cp', d.most_common(8))
print('cpp!=cp', sum(1 for r in rows if r['cp'] is not None and abs(r['cpp']-r['cp'])>0.0011))
# relation of cpp-cp to the gap
x=[r for r in g if r['cp'] is not None and abs(r['cpp']-r['cp'])>0.0011]
print('cpp!=cp & gap>0.01', sum(abs(r['gap'])>0.01 for r in x), 'of', len(x))
print('gap>0.01 & cpp==cp', sum(1 for r in g if abs(r['gap'])>0.01 and r['cp'] is not None and abs(r['cpp']-r['cp'])<=0.0011))
print('retain_power vs cp mismatch', sum(1 for r in rows if r['cp'] is not None and r['rp'] is not None and abs(r['cp']-r['rp'])>0.0011))
import pickle; pickle.dump([{k:v for k,v in r.items() if k not in('n',)} for r in rows], open('/tmp/eu4research/cache/r10_rows.pkl','wb'))
