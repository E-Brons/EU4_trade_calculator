"""R11 Q3: is the ship multiplier related to the ships' home port (ship.home province) being inside the node?"""
import sys,pickle,json; sys.path.insert(0,'scripts/research')
exec(open('scripts/research/r11_r14_fleetflags.py').read().split("unique=0")[0])
per=pickle.load(open('/tmp/eu4research/cache/r11_ratio.pkl','rb'))
ratio={(sid,tag,node):r for (sid,tag),v in per.items() for node,r,n,sp in v}
tn=json.load(open('data/tradenodes.json'))['nodes']; mem={k:set(v['member_provinces']) for k,v in tn.items()}
# which node holds each province (land provinces)
prov2node={}
for k,s in mem.items():
    for p in s: prov2node[p]=k
res=Counter(); detail=[]
for e in common.entries():
    if e['id'] not in ('S79','S80'): continue
    order=[n['definitions'] for n in common.nodes(e)]
    cs=common.block(e,'countries')
    for (sid,tag,node),r in ratio.items():
        if sid!=e['id']: continue
        nv=cs[tag]['navy']; nv=nv if isinstance(nv,list) else [nv]
        homes=Counter()
        for f in nv:
            m=f.get('mission')
            if not(isinstance(m,dict) and isinstance(m.get('protect_mission'),dict)): continue
            pm=m['protect_mission']
            if order[int(pm['node'])-1]!=node or 'on_my_way' not in pm: continue
            for s in (f['ship'] if isinstance(f['ship'],list) else [f['ship']]):
                homes[prov2node.get(s['home'],'?')==node]+=1
        key=(r!=1.0, 'all_home_in_node' if homes[False]==0 else ('none' if homes[True]==0 else 'mixed'))
        res[key]+=1
        if r!=1.0: detail.append((sid,tag,node,r,dict(homes)))
print(res)
for d in detail: print(d)
