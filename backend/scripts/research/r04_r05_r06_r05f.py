import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import r04_r05_r06_flat as fl, pickle, collections
rows, nodes = fl.load()
nidx = {(n['sid'], n['definitions']): n for n in nodes}
out = pickle.load(open('/tmp/eu4research/cache/r05_single.pkl','rb'))
big = [o for o in out if o['pD']>=10]
def cross(name, f):
    d = collections.defaultdict(lambda:[0,0])
    for o in big: d[f(o)][0 if o['prev']>0 else 1]+=1
    print(name, dict(sorted(d.items(), key=lambda kv:str(kv[0]))))
cross('B pull_power>0', lambda o: nidx[(o['sid'],o['B'])].get('pull_power',0)>0)
cross('B outgoing>0', lambda o: nidx[(o['sid'],o['B'])].get('outgoing',0)>0)
cross('B retention==1', lambda o: nidx[(o['sid'],o['B'])].get('retention')==1)
cross('B has entries w/ any prev', lambda o: any(True for r in []))
# B 'type'? is B ever missing 'pull_power' key
cross('B local_value>0', lambda o: nidx[(o['sid'],o['B'])].get('local_value',0)>0)
cross('B num_collectors>0', lambda o: nidx[(o['sid'],o['B'])].get('num_collectors',0)>0)

idx = {(r['sid'],r['node'],r['tag']): r for r in rows if set(r)-{'max_demand','sid','node','tag','date'}}
from app.trade import game_data
g = game_data.graph()
import functools
@functools.lru_cache(None)
def down(n):
    s=set()
    for t in g.outgoing(n): s.add(t); s|=down(t)
    return frozenset(s)
coll = collections.defaultdict(set)
for (sid,node,tag),r in idx.items():
    if 'total' in r: coll[(sid,tag)].add(node)
cross('collects at D', lambda o: 'total' in idx[(o['sid'],o['D'],o['tag'])])
cross('collects at D or beyond', lambda o: bool(coll[(o['sid'],o['tag'])] & ({o['D']}|down(o['D']))))
cross('collects anywhere', lambda o: bool(coll[(o['sid'],o['tag'])]))
cross('has_trader at D', lambda o: bool(idx[(o['sid'],o['D'],o['tag'])].get('has_trader')))
# cases not explained by 'collects at D or beyond'
bad = [o for o in big if (o['prev']>0) != bool(coll[(o['sid'],o['tag'])] & ({o['D']}|down(o['D'])))]
print(len(bad), collections.Counter((o['B'],o['D'],o['tag'], o['prev']>0) for o in bad).most_common(12))

print('--- key presence at B')
for key in ('pull_power','outgoing','steer_power','value_added_outgoing','retain_power','local_value','current','total'):
    cross('B has key '+key, lambda o,key=key: key in nidx[(o['sid'],o['B'])])

print('--- link evidence at D.incoming')
from common import as_list
def has_inc(o):
    n = nidx[(o['sid'],o['D'])]
    order = n['order']
    srcs = set()
    for i in as_list(n.get('incoming')):
        if isinstance(i, dict) and 0 < int(i['from']) <= len(order): srcs.add(order[int(i['from'])-1])
    return o['B'] in srcs
cross('D.incoming lists B', has_inc)
cross('B has steer_power len == graph outdeg', lambda o: len(as_list(nidx[(o['sid'],o['B'])].get('steer_power')))==len(g.outgoing(o['B'])))

print('--- link weight at B')
def w(o):
    sp = as_list(nidx[(o['sid'],o['B'])].get('steer_power'))
    i = list(g.outgoing(o['B'])).index(o['D'])
    return sp[i] if i < len(sp) else None
cross('steer weight of link B->D > 0', lambda o: (w(o) or 0) > 0)
cross('steer weight is None/0 vs positive', lambda o: 'pos' if (w(o) or 0)>0 else ('zero' if w(o)==0 else 'none'))
def inc_val(o):
    n = nidx[(o['sid'],o['D'])]; order=n['order']
    for i in as_list(n.get('incoming')):
        if isinstance(i, dict) and order[int(i['from'])-1]==o['B']: return i['value']
cross('D.incoming value from B > 0', lambda o: (inc_val(o) or 0) > 0)

print('--- exceptions: P but weight 0')
ex = [o for o in big if o['prev']>0 and (w(o) or 0)==0]
print(len(ex))
print(collections.Counter((o['B'],o['D'], nidx[(o['sid'],o['B'])].get('steer_power') and tuple(nidx[(o['sid'],o['B'])]['steer_power'])) for o in ex).most_common(10))
print(collections.Counter(o['sid'] for o in ex).most_common(5))
# the zero cases: weights
z = [o for o in big if o['prev']==0]
print(collections.Counter(tuple(as_list(nidx[(o['sid'],o['B'])].get('steer_power'))) for o in z).most_common(8))
# what is steer weight array when node B has link weight zero
