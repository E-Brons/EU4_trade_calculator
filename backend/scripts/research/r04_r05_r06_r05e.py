import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import common, pickle, collections
out = pickle.load(open('/tmp/eu4research/cache/r05_single.pkl','rb'))
big = [o for o in out if o['pD']>=10]
ents = {e['id']: e for e in common.entries()}
cc = {}
def info(sid, tag):
    if sid not in cc: cc[sid] = common.block(ents[sid], 'countries')
    c = cc[sid].get(tag, {})
    t = c.get('technology', {}) if isinstance(c.get('technology'), dict) else {}
    return dict(tg=c.get('technology_group'), dip=t.get('dip_tech'), adm=t.get('adm_tech'), mil=t.get('mil_tech'),
                nm=len(c.get('merchants',{}).get('envoy',[])) if isinstance(c.get('merchants'),dict) and isinstance(c.get('merchants',{}).get('envoy'),list) else None,
                colonial=c.get('colonial_parent') or c.get('is_colonial') , overlord=c.get('overlord'), ncities=c.get('num_of_cities'))
ct = collections.Counter(); 
tgs = collections.defaultdict(lambda:[0,0])
for o in big:
    i = info(o['sid'], o['tag'])
    tgs[i['tg']][0 if o['prev']>0 else 1] += 1
print({k:v for k,v in sorted(tgs.items(), key=lambda kv:-sum(kv[1]))})
# the zero cases by tech group, plus which pairs
z = [o for o in big if o['prev']==0]
print(collections.Counter((info(o['sid'],o['tag'])['tg']) for o in z))
pickle.dump(None, open('/tmp/eu4research/cache/_dummy','wb'))

mixed = {('california','girin'),('california','mexico'),('patagonia','cuiaba'),('amazonas_node','cuiaba'),('polynesia_node','nippon'),('australia','the_moluccas'),('african_great_lakes','zanzibar'),('cape_of_good_hope','ivory_coast'),('brazil','ivory_coast'),('katsina','tunis'),('polynesia_node','panama'),('carribean_trade','chesapeake_bay'),('st_lawrence','north_sea'),('carribean_trade','bordeaux'),('ivory_coast','bordeaux'),('st_lawrence','bordeaux'),('ivory_coast','sevilla'),('carribean_trade','sevilla'),('chesapeake_bay','english_channel'),('ivory_coast','english_channel'),('cuiaba','lima'),('amazonas_node','carribean_trade'),('mississippi_river','carribean_trade'),('mexico','carribean_trade'),('ivory_coast','carribean_trade')}
mx = [o for o in big if (o['B'],o['D']) in mixed]
print('mixed-pair cases', len(mx))
def cross(name, f):
    d = collections.defaultdict(lambda:[0,0])
    for o in mx:
        d[f(o)][0 if o['prev']>0 else 1] += 1
    print(name, dict(sorted(d.items(), key=lambda kv: str(kv[0]))))
cross('dip', lambda o: info(o['sid'],o['tag'])['dip'])
cross('has_B', lambda o: o['has_B'])
cross('D_trader', lambda o: o['D_trader'])
cross('D_cap', lambda o: o['D_has_capital'])
cross('overlord', lambda o: bool(info(o['sid'],o['tag'])['overlord']))
cross('date', lambda o: o['sid'])

print('----')
for pair in [('california','mexico'),('cape_of_good_hope','ivory_coast')]:
    L = [o for o in mx if (o['B'],o['D'])==pair]
    d = collections.defaultdict(lambda:[0,0])
    for o in L:
        i = info(o['sid'],o['tag']); d[(o['tag'], i['tg'], i['dip'])][0 if o['prev']>0 else 1]+=1
    print(pair); [print('  ',k,v) for k,v in sorted(d.items(), key=lambda kv:(kv[0][0],str(kv[0][2])))]

print('==== per country-save')
cs = {}
for o in mx:
    cs.setdefault((o['sid'],o['tag']), set()).add(o['prev']>0)
rows2=[]
for (sid,tag),flags in cs.items():
    c = cc.setdefault(sid, common.block(ents[sid],'countries')).get(tag,{})
    inst = c.get('institutions')
    t = c.get('technology',{})
    rows2.append((sid,tag,flags,inst,t.get('dip_tech'),t.get('adm_tech'),t.get('mil_tech'), c.get('trade_port'), c.get('capital')))
print(collections.Counter(tuple(sorted(f)) for _,_,f,*_ in rows2))
# P vs zero by institution vector
d = collections.defaultdict(lambda:[0,0])
for sid,tag,f,inst,dip,adm,mil,tp,cap in rows2:
    if len(f)==1: d[str(inst)][0 if True in f else 1]+=1
print(dict(d))
d = collections.defaultdict(lambda:[0,0])
for sid,tag,f,inst,dip,adm,mil,tp,cap in rows2:
    if len(f)==1: d[(min(dip,adm,mil))][0 if True in f else 1]+=1
print('min tech', dict(sorted(d.items())))
d = collections.defaultdict(lambda:[0,0])
for sid,tag,f,inst,dip,adm,mil,tp,cap in rows2:
    if len(f)==1: d[(dip,adm,mil)][0 if True in f else 1]+=1
print('tech triples where both', {k:v for k,v in d.items() if v[0] and v[1]})
